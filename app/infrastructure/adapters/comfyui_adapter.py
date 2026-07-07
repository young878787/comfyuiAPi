"""ComfyUI API adapter — supports both UI-format and API-format workflows."""

import json
import urllib.request
import urllib.parse
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import httpx

from app.config import settings
from app.domain.exceptions import ImageGenerationError, APIError
from app.infrastructure.retry_utils import retry_async

logger = logging.getLogger(__name__)


class ComfyUIAdapter:
    """Adapter for ComfyUI API."""

    def __init__(self):
        """Initialize the adapter with configuration."""
        self.server_address = settings.comfyui_api_url.replace("http://", "")
        self.workflow_path = settings.workflow_path
        self.timeout = 300  # 5 minutes

    # ------------------------------------------------------------------
    # Workflow loading
    # ------------------------------------------------------------------

    def load_workflow(self, workflow_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load ComfyUI workflow from JSON file.

        Supports two formats:
          - UI format:  dict with a "nodes" list (produced by ComfyUI GUI export)
          - API format: dict keyed by node-ID strings (produced by ComfyUI API export)

        Returns:
            dict: Raw workflow data

        Raises:
            ImageGenerationError: If the file cannot be loaded or parsed
        """
        target_path = workflow_path or self.workflow_path
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)

            fmt = "UI" if self._is_ui_format(workflow) else "API"
            logger.info(
                "Workflow loaded (%s format)",
                fmt,
                extra={"workflow_path": str(target_path)},
            )
            return workflow

        except FileNotFoundError:
            logger.error(
                "Workflow file not found",
                extra={"workflow_path": str(target_path)},
            )
            raise ImageGenerationError(
                f"Workflow file not found: {target_path}"
            )

        except json.JSONDecodeError as e:
            logger.error(
                "Invalid workflow JSON",
                extra={"workflow_path": str(target_path), "error": str(e)},
            )
            raise ImageGenerationError(f"Invalid workflow JSON: {str(e)}")

    # ------------------------------------------------------------------
    # Format detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_ui_format(workflow: Dict[str, Any]) -> bool:
        """Return True if the workflow is in ComfyUI UI (GUI export) format."""
        return "nodes" in workflow

    # ------------------------------------------------------------------
    # Parameter update — unified entry point
    # ------------------------------------------------------------------

    def update_workflow_params(
        self,
        workflow: Dict[str, Any],
        positive_prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        seed: int,
        sampler: str,
        scheduler: str,
        checkpoint: Optional[str] = None,
        input_image_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inject generation parameters into the workflow.

        Automatically selects the correct update strategy based on the
        detected workflow format (UI vs API).
        """
        if self._is_ui_format(workflow):
            return self._update_ui_format_params(
                workflow,
                positive_prompt,
                negative_prompt,
                width,
                height,
                steps,
                cfg,
                seed,
                sampler,
                scheduler,
                checkpoint,
                input_image_name,
            )
        return self._update_api_format_params(
            workflow,
            positive_prompt,
            negative_prompt,
            width,
            height,
            steps,
            cfg,
            seed,
            sampler,
            scheduler,
            checkpoint,
            input_image_name,
        )

    def _update_ui_format_params(
        self,
        workflow: Dict[str, Any],
        positive_prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        seed: int,
        sampler: str,
        scheduler: str,
        checkpoint: Optional[str] = None,
        input_image_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update parameters for UI-format workflows (e.g. qwen image.json).

        Node IDs are fixed by the saved workflow:
          6  -> CLIPTextEncode positive
          7  -> CLIPTextEncode negative
          3  -> KSampler
          58 -> EmptySD3LatentImage
        """
        for node in workflow["nodes"]:
            nid = node["id"]
            ntype = node.get("type", "")

            if nid == 6 and ntype == "CLIPTextEncode":
                node["widgets_values"][0] = positive_prompt

            elif nid == 7 and ntype == "CLIPTextEncode":
                node["widgets_values"][0] = negative_prompt

            elif nid == 3 and ntype == "KSampler":
                # [seed, control_after_generate, steps, cfg, sampler, scheduler, denoise]
                node["widgets_values"][0] = seed
                node["widgets_values"][2] = steps
                node["widgets_values"][3] = cfg
                node["widgets_values"][4] = sampler
                node["widgets_values"][5] = scheduler

            elif nid == 58 and ntype == "EmptySD3LatentImage":
                # [width, height, batch_size]
                node["widgets_values"][0] = width
                node["widgets_values"][1] = height

            elif ntype == "LoadImage" and input_image_name:
                if "widgets_values" in node and len(node["widgets_values"]) > 0:
                    node["widgets_values"][0] = input_image_name

            # Dynamically replace checkpoint model if provided
            if checkpoint:
                if ntype == "CheckpointLoaderSimple":
                    if "widgets_values" in node and len(node["widgets_values"]) > 0:
                        node["widgets_values"][0] = checkpoint
                elif ntype == "UNETLoader":
                    if "widgets_values" in node and len(node["widgets_values"]) > 0:
                        node["widgets_values"][0] = checkpoint
                elif ntype == "UNet loader with Name (Image Saver)":
                    if "widgets_values" in node and len(node["widgets_values"]) > 0:
                        node["widgets_values"][0] = checkpoint

        logger.info(
            "Workflow parameters updated (UI format)",
            extra={
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
                "checkpoint": checkpoint,
                "input_image_name": input_image_name,
            },
        )
        return workflow

    def _update_api_format_params(
        self,
        workflow: Dict[str, Any],
        positive_prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        seed: int,
        sampler: str,
        scheduler: str,
        checkpoint: Optional[str] = None,
        input_image_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update parameters for API-format workflows (e.g. Anima.json).

        Nodes are identified by class_type + _meta.title rather than
        hard-coded IDs, making this robust to future workflow changes.
        """
        # Identify positive/negative text source nodes (e.g. PrimitiveStringMultiline linked to CLIPTextEncode)
        pos_source_id = None
        neg_source_id = None

        for nid, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue
            class_type = node_data.get("class_type", "")
            meta_title = node_data.get("_meta", {}).get("title", "")
            inputs = node_data.get("inputs", {})

            if class_type == "CLIPTextEncode":
                title_lower = meta_title.lower()
                text_input = inputs.get("text")
                if isinstance(text_input, list) and len(text_input) > 0:
                    src_id = str(text_input[0])
                    if "positive" in title_lower:
                        pos_source_id = src_id
                    elif "negative" in title_lower:
                        neg_source_id = src_id

        for nid, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            meta_title = node_data.get("_meta", {}).get("title", "")
            inputs = node_data.get("inputs", {})

            # Update string source nodes directly if they exist
            if nid == pos_source_id:
                inputs["value"] = positive_prompt
                continue
            if nid == neg_source_id:
                inputs["value"] = negative_prompt
                continue

            if class_type == "CLIPTextEncode":
                title_lower = meta_title.lower()
                if "positive" in title_lower:
                    inputs["text"] = positive_prompt
                elif "negative" in title_lower:
                    inputs["text"] = negative_prompt

            elif class_type == "KSampler":
                inputs["seed"] = seed
                inputs["steps"] = steps
                inputs["cfg"] = cfg
                inputs["sampler_name"] = sampler
                inputs["scheduler"] = scheduler

            elif class_type == "Input Parameters (Image Saver)":
                inputs["seed"] = seed
                inputs["steps"] = steps
                inputs["cfg"] = cfg
                inputs["sampler"] = sampler
                inputs["scheduler"] = scheduler

            elif class_type in ("EmptyLatentImage", "EmptySD3LatentImage"):
                inputs["width"] = width
                inputs["height"] = height

            elif class_type == "LoadImage" and input_image_name:
                inputs["image"] = input_image_name

            # Dynamically replace checkpoint model if provided
            if checkpoint:
                if class_type == "CheckpointLoaderSimple":
                    inputs["ckpt_name"] = checkpoint
                elif class_type == "UNETLoader":
                    inputs["unet_name"] = checkpoint
                elif class_type == "UNet loader with Name (Image Saver)":
                    inputs["unet_name"] = checkpoint

        logger.info(
            "Workflow parameters updated (API format)",
            extra={
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
                "checkpoint": checkpoint,
                "input_image_name": input_image_name,
            },
        )
        return workflow

    # ------------------------------------------------------------------
    # UI-format conversion
    # ------------------------------------------------------------------

    def convert_workflow_to_api_format(
        self, workflow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert a UI-format workflow to ComfyUI API format.

        Only required for workflows exported from the ComfyUI GUI.
        API-format workflows (e.g. Anima.json) are passed through as-is.
        """
        api_prompt: Dict[str, Any] = {}

        # Build link map: link_id -> [source_node_id_str, output_index]
        link_map: Dict[int, list] = {}
        for link in workflow.get("links", []):
            link_id = link[0]
            source_node_id = link[1]
            source_output_index = link[2]
            link_map[link_id] = [str(source_node_id), source_output_index]

        for node in workflow.get("nodes", []):
            node_id = str(node["id"])
            node_type = node["type"]

            if node_type in ("Note", "MarkdownNote"):
                continue

            inputs: Dict[str, Any] = {}
            widget_inputs: list = []

            for input_item in node.get("inputs", []):
                input_name = input_item["name"]
                link_id = input_item.get("link")
                if link_id is not None and link_id in link_map:
                    inputs[input_name] = link_map[link_id]
                else:
                    widget_inputs.append(input_name)

            if "widgets_values" in node and widget_inputs:
                widget_values = node["widgets_values"]
                if node_type == "KSampler":
                    inputs["seed"] = widget_values[0]
                    inputs["steps"] = widget_values[2]
                    inputs["cfg"] = widget_values[3]
                    inputs["sampler_name"] = widget_values[4]
                    inputs["scheduler"] = widget_values[5]
                    inputs["denoise"] = widget_values[6]
                else:
                    for i, name in enumerate(widget_inputs):
                        if i < len(widget_values):
                            inputs[name] = widget_values[i]

            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": inputs,
            }

        return api_prompt

    # ------------------------------------------------------------------
    # ComfyUI queue
    # ------------------------------------------------------------------

    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        Queue a prompt on the ComfyUI server.

        Automatically converts UI-format workflows; passes API-format
        workflows directly.

        Returns:
            str: Prompt ID assigned by ComfyUI

        Raises:
            APIError: If the HTTP request fails
        """
        if self._is_ui_format(workflow):
            api_format = self.convert_workflow_to_api_format(workflow)
        else:
            api_format = workflow  # already API format

        prompt = {"prompt": api_format}

        async def _do_queue():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"http://{self.server_address}/prompt",
                    json=prompt,
                )
                response.raise_for_status()
                result = response.json()
                return result["prompt_id"]

        try:
            prompt_id = await retry_async(_do_queue, max_retries=3, delay=1.0, backoff=2.0)

            logger.info(
                "Prompt queued successfully", extra={"prompt_id": prompt_id}
            )
            return prompt_id

        except httpx.HTTPStatusError as e:
            logger.error(
                "ComfyUI API HTTP error",
                extra={"status_code": e.response.status_code, "reason": e.response.reason_phrase},
                exc_info=True,
            )
            raise APIError(f"ComfyUI API error: {e.response.status_code} - {e.response.reason_phrase}")

        except Exception as e:
            logger.error(
                "ComfyUI API unexpected error",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise APIError(f"ComfyUI API error: {str(e)}")

    # ------------------------------------------------------------------
    # Polling / image retrieval
    # ------------------------------------------------------------------

    async def wait_for_completion(self, prompt_id: str) -> Dict[str, Any]:
        """
        Poll ComfyUI history until the prompt finishes.

        Returns:
            dict: History entry for this prompt_id

        Raises:
            ImageGenerationError: On timeout
        """
        start_time = datetime.now()
        poll_interval = 2

        while True:
            elapsed = (datetime.now() - start_time).total_seconds()

            if elapsed > self.timeout:
                logger.error(
                    "Image generation timeout",
                    extra={"prompt_id": prompt_id, "timeout": self.timeout},
                )
                raise ImageGenerationError("Image generation timeout")

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"http://{self.server_address}/history/{prompt_id}")
                    if resp.status_code == 200:
                        history = resp.json()
                        if prompt_id in history:
                            logger.info(
                                "Image generation completed",
                                extra={"prompt_id": prompt_id, "elapsed": elapsed},
                            )
                            return history[prompt_id]

            except Exception as e:
                logger.warning(
                    "Failed to get history",
                    extra={"prompt_id": prompt_id, "error": str(e)},
                )

            await asyncio.sleep(poll_interval)

    async def get_image(
        self, filename: str, subfolder: str, folder_type: str
    ) -> bytes:
        """
        Download a generated image from ComfyUI.

        Returns:
            bytes: Raw image data

        Raises:
            ImageGenerationError: If the download fails
        """
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}

        async def _do_download():
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"http://{self.server_address}/view",
                    params=data
                )
                resp.raise_for_status()
                return resp.content

        try:
            image_data = await retry_async(_do_download, max_retries=3, delay=1.0, backoff=2.0)

            logger.info(
                "Image downloaded successfully",
                extra={"image_filename": filename, "image_size": len(image_data)},
            )
            return image_data

        except Exception as e:
            logger.error(
                "Failed to download image",
                extra={"image_filename": filename, "error_message": str(e)},
                exc_info=True,
            )
            raise ImageGenerationError(f"Failed to download image: {str(e)}")

    async def upload_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Upload an image to ComfyUI input folder via ComfyUI API /upload/image.
        
        Returns:
            dict: ComfyUI response containing name, subfolder, and type
        """
        url = f"http://{self.server_address}/upload/image"
        
        async def _do_upload():
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {
                    "image": (filename, image_bytes, "image/png")
                }
                response = await client.post(url, files=files)
                response.raise_for_status()
                return response.json()

        try:
            result = await retry_async(_do_upload, max_retries=3, delay=1.0, backoff=2.0)
            logger.info("Image uploaded to ComfyUI successfully: %s", result.get("name"))
            return result
        except Exception as e:
            logger.error("Failed to upload image to ComfyUI", exc_info=True)
            raise APIError(f"Failed to upload image to ComfyUI: {str(e)}")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def generate_image(
        self,
        positive_prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        seed: int,
        sampler: str,
        scheduler: str,
        workflow_path: Optional[str] = None,
        checkpoint: Optional[str] = None,
        input_image_name: Optional[str] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Full image generation pipeline: load → update → queue → poll → download.

        Returns:
            tuple: (image_bytes, generation_info_dict)

        Raises:
            ImageGenerationError: On any failure
        """
        try:
            workflow = self.load_workflow(workflow_path)
            workflow = self.update_workflow_params(
                workflow,
                positive_prompt,
                negative_prompt,
                width,
                height,
                steps,
                cfg,
                seed,
                sampler,
                scheduler,
                checkpoint,
                input_image_name,
            )

            prompt_id = await self.queue_prompt(workflow)
            history = await self.wait_for_completion(prompt_id)

            # Find the first SaveImage node output
            outputs = history.get("outputs", {})
            image_info = None
            for node_output in outputs.values():
                if "images" in node_output:
                    image_info = node_output["images"][0]
                    break

            if not image_info:
                raise ImageGenerationError("No image found in ComfyUI output")

            image_data = await self.get_image(
                image_info["filename"],
                image_info.get("subfolder", ""),
                image_info.get("type", "output"),
            )

            generation_info = {
                "prompt_id": prompt_id,
                "filename": image_info["filename"],
                "seed": seed,
            }

            return image_data, generation_info

        except Exception as e:
            logger.error(
                "Image generation failed", extra={"error": str(e)}, exc_info=True
            )
            if isinstance(e, (ImageGenerationError, APIError)):
                raise
            raise ImageGenerationError(f"Image generation failed: {str(e)}")

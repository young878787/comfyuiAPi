"""ComfyUI API adapter — supports both UI-format and API-format workflows."""

import json
import urllib.request
import urllib.parse
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

from app.config import settings
from app.domain.exceptions import ImageGenerationError, APIError

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

    def load_workflow(self) -> Dict[str, Any]:
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
        try:
            with open(self.workflow_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)

            fmt = "UI" if self._is_ui_format(workflow) else "API"
            logger.info(
                "Workflow loaded (%s format)",
                fmt,
                extra={"workflow_path": str(self.workflow_path)},
            )
            return workflow

        except FileNotFoundError:
            logger.error(
                "Workflow file not found",
                extra={"workflow_path": str(self.workflow_path)},
            )
            raise ImageGenerationError(
                f"Workflow file not found: {self.workflow_path}"
            )

        except json.JSONDecodeError as e:
            logger.error(
                "Invalid workflow JSON",
                extra={"workflow_path": str(self.workflow_path), "error": str(e)},
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

        logger.info(
            "Workflow parameters updated (UI format)",
            extra={
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
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
    ) -> Dict[str, Any]:
        """
        Update parameters for API-format workflows (e.g. Anima.json).

        Nodes are identified by class_type + _meta.title rather than
        hard-coded IDs, making this robust to future workflow changes.
        """
        for node_data in workflow.values():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            meta_title = node_data.get("_meta", {}).get("title", "")
            inputs = node_data.get("inputs", {})

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

            elif class_type in ("EmptyLatentImage", "EmptySD3LatentImage"):
                inputs["width"] = width
                inputs["height"] = height

        logger.info(
            "Workflow parameters updated (API format)",
            extra={
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
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

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
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
        data = json.dumps(prompt).encode("utf-8")

        req = urllib.request.Request(
            f"http://{self.server_address}/prompt",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read())
            prompt_id = result["prompt_id"]

            logger.info(
                "Prompt queued successfully", extra={"prompt_id": prompt_id}
            )
            return prompt_id

        except urllib.error.HTTPError as e:
            logger.error(
                "ComfyUI API HTTP error",
                extra={"status_code": e.code, "reason": e.reason},
                exc_info=True,
            )
            raise APIError(f"ComfyUI API error: {e.code} - {e.reason}")

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
                with urllib.request.urlopen(
                    f"http://{self.server_address}/history/{prompt_id}"
                ) as resp:
                    history = json.loads(resp.read())

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

    def get_image(
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
        url_values = urllib.parse.urlencode(data)

        try:
            with urllib.request.urlopen(
                f"http://{self.server_address}/view?{url_values}"
            ) as resp:
                image_data = resp.read()

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
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Full image generation pipeline: load → update → queue → poll → download.

        Returns:
            tuple: (image_bytes, generation_info_dict)

        Raises:
            ImageGenerationError: On any failure
        """
        try:
            workflow = self.load_workflow()
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
            )

            prompt_id = self.queue_prompt(workflow)
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

            image_data = self.get_image(
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

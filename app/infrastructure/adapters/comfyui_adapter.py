"""ComfyUI API adapter."""

import json
import urllib.request
import urllib.parse
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
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
        self.timeout = 300  # 5 minutes timeout
    
    def load_workflow(self) -> Dict[str, Any]:
        """
        Load ComfyUI workflow from JSON file.
        
        Returns:
            dict: Workflow data
            
        Raises:
            ImageGenerationError: If workflow file cannot be loaded
        """
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            logger.info("Workflow loaded successfully", extra={
                "workflow_path": str(self.workflow_path)
            })
            
            return workflow
            
        except FileNotFoundError:
            logger.error("Workflow file not found", extra={
                "workflow_path": str(self.workflow_path)
            })
            raise ImageGenerationError(f"Workflow file not found: {self.workflow_path}")
            
        except json.JSONDecodeError as e:
            logger.error("Invalid workflow JSON", extra={
                "workflow_path": str(self.workflow_path),
                "error": str(e)
            })
            raise ImageGenerationError(f"Invalid workflow JSON: {str(e)}")
    
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
        scheduler: str
    ) -> Dict[str, Any]:
        """
        Update workflow parameters.
        
        Args:
            workflow: Workflow data
            positive_prompt: Positive prompt
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Sampling steps
            cfg: CFG scale
            seed: Random seed
            sampler: Sampler name
            scheduler: Scheduler name
            
        Returns:
            dict: Updated workflow
        """
        for node in workflow['nodes']:
            # Update positive prompt (node 6)
            if node['id'] == 6 and node['type'] == 'CLIPTextEncode':
                node['widgets_values'][0] = positive_prompt
            
            # Update negative prompt (node 7)
            if node['id'] == 7 and node['type'] == 'CLIPTextEncode':
                node['widgets_values'][0] = negative_prompt
            
            # Update KSampler params (node 3)
            if node['id'] == 3 and node['type'] == 'KSampler':
                # widgets_values: [seed, control_after_generate, steps, cfg, sampler, scheduler, denoise]
                node['widgets_values'][0] = seed
                node['widgets_values'][2] = steps
                node['widgets_values'][3] = cfg
                node['widgets_values'][4] = sampler
                node['widgets_values'][5] = scheduler
            
            # Update image size (node 58)
            if node['id'] == 58 and node['type'] == 'EmptySD3LatentImage':
                # widgets_values: [width, height, batch_size]
                node['widgets_values'][0] = width
                node['widgets_values'][1] = height
        
        logger.info("Workflow parameters updated", extra={
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "seed": seed
        })
        
        return workflow
    
    def convert_workflow_to_api_format(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert workflow to ComfyUI API format.
        
        Args:
            workflow: Workflow data
            
        Returns:
            dict: API format prompt
        """
        api_prompt = {}
        
        # Build link map
        link_map = {}
        for link in workflow.get('links', []):
            link_id = link[0]
            source_node_id = link[1]
            source_output_index = link[2]
            link_map[link_id] = [str(source_node_id), source_output_index]
        
        # Convert nodes
        for node in workflow.get('nodes', []):
            node_id = str(node['id'])
            node_type = node['type']
            
            # Skip comment nodes
            if node_type in ['Note', 'MarkdownNote']:
                continue
            
            inputs = {}
            widget_inputs = []
            
            # Process inputs
            for input_item in node.get('inputs', []):
                input_name = input_item['name']
                
                if 'link' in input_item and input_item['link'] is not None:
                    link_id = input_item['link']
                    if link_id in link_map:
                        inputs[input_name] = link_map[link_id]
                else:
                    widget_inputs.append(input_name)
            
            # Map widget values
            if 'widgets_values' in node and widget_inputs:
                widget_values = node['widgets_values']
                
                if node_type == 'KSampler':
                    inputs['seed'] = widget_values[0]
                    inputs['steps'] = widget_values[2]
                    inputs['cfg'] = widget_values[3]
                    inputs['sampler_name'] = widget_values[4]
                    inputs['scheduler'] = widget_values[5]
                    inputs['denoise'] = widget_values[6]
                else:
                    for i, input_name in enumerate(widget_inputs):
                        if i < len(widget_values):
                            inputs[input_name] = widget_values[i]
            
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": inputs
            }
        
        return api_prompt
    
    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        Queue prompt to ComfyUI server.
        
        Args:
            workflow: Workflow data
            
        Returns:
            str: Prompt ID
            
        Raises:
            APIError: If API call fails
        """
        api_format = self.convert_workflow_to_api_format(workflow)
        prompt = {"prompt": api_format}
        data = json.dumps(prompt).encode('utf-8')
        
        req = urllib.request.Request(
            f"http://{self.server_address}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read())
            prompt_id = result['prompt_id']
            
            logger.info("Prompt queued successfully", extra={
                "prompt_id": prompt_id
            })
            
            return prompt_id
            
        except urllib.error.HTTPError as e:
            logger.error("ComfyUI API HTTP error", extra={
                "status_code": e.code,
                "reason": e.reason
            }, exc_info=True)
            raise APIError(f"ComfyUI API error: {e.code} - {e.reason}")
            
        except Exception as e:
            logger.error("ComfyUI API unexpected error", extra={
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"ComfyUI API error: {str(e)}")
    
    async def wait_for_completion(self, prompt_id: str) -> Dict[str, Any]:
        """
        Wait for image generation to complete.
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            dict: History data
            
        Raises:
            ImageGenerationError: If generation fails or times out
        """
        start_time = datetime.now()
        poll_interval = 2  # seconds
        
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed > self.timeout:
                logger.error("Image generation timeout", extra={
                    "prompt_id": prompt_id,
                    "timeout": self.timeout
                })
                raise ImageGenerationError("Image generation timeout")
            
            try:
                with urllib.request.urlopen(
                    f"http://{self.server_address}/history/{prompt_id}"
                ) as response:
                    history = json.loads(response.read())
                
                if prompt_id in history:
                    logger.info("Image generation completed", extra={
                        "prompt_id": prompt_id,
                        "elapsed_time": elapsed
                    })
                    return history[prompt_id]
                
            except Exception as e:
                logger.warning("Failed to get history", extra={
                    "prompt_id": prompt_id,
                    "error": str(e)
                })
            
            await asyncio.sleep(poll_interval)
    
    def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """
        Download generated image from ComfyUI.
        
        Args:
            filename: Image filename
            subfolder: Subfolder name
            folder_type: Folder type
            
        Returns:
            bytes: Image data
            
        Raises:
            ImageGenerationError: If image download fails
        """
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        
        try:
            with urllib.request.urlopen(
                f"http://{self.server_address}/view?{url_values}"
            ) as response:
                image_data = response.read()
            
            logger.info("Image downloaded successfully", extra={
                "image_filename": filename,
                "image_size": len(image_data)
            })
            
            return image_data
            
        except Exception as e:
            logger.error("Failed to download image", extra={
                "image_filename": filename,
                "error_message": str(e)
            }, exc_info=True)
            raise ImageGenerationError(f"Failed to download image: {str(e)}")
    
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
        scheduler: str
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate image using ComfyUI.
        
        Args:
            positive_prompt: Positive prompt
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Sampling steps
            cfg: CFG scale
            seed: Random seed
            sampler: Sampler name
            scheduler: Scheduler name
            
        Returns:
            tuple: (image_data, generation_info)
            
        Raises:
            ImageGenerationError: If generation fails
        """
        try:
            # Load and update workflow
            workflow = self.load_workflow()
            workflow = self.update_workflow_params(
                workflow, positive_prompt, negative_prompt,
                width, height, steps, cfg, seed, sampler, scheduler
            )
            
            # Queue prompt
            prompt_id = self.queue_prompt(workflow)
            
            # Wait for completion
            history = await self.wait_for_completion(prompt_id)
            
            # Extract image info
            outputs = history.get('outputs', {})
            
            # Find SaveImage node (usually node 60)
            image_info = None
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    image_info = node_output['images'][0]
                    break
            
            if not image_info:
                raise ImageGenerationError("No image found in ComfyUI output")
            
            # Download image
            image_data = self.get_image(
                image_info['filename'],
                image_info.get('subfolder', ''),
                image_info.get('type', 'output')
            )
            
            generation_info = {
                "prompt_id": prompt_id,
                "filename": image_info['filename'],
                "seed": seed,
            }
            
            return image_data, generation_info
            
        except Exception as e:
            logger.error("Image generation failed", extra={
                "error": str(e)
            }, exc_info=True)
            
            if isinstance(e, (ImageGenerationError, APIError)):
                raise
            else:
                raise ImageGenerationError(f"Image generation failed: {str(e)}")

"""Image service for image generation management."""

import logging
import random
from datetime import datetime
from typing import Optional, Tuple

from app.domain.models import ImageMetadata
from app.infrastructure.repositories.image_repository import ImageRepository
from app.infrastructure.adapters.comfyui_adapter import ComfyUIAdapter
from app.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    """Service for managing image generation."""
    
    def __init__(
        self,
        image_repository: ImageRepository,
        comfyui_adapter: ComfyUIAdapter
    ):
        """
        Initialize service with dependencies.
        
        Args:
            image_repository: Image repository
            comfyui_adapter: ComfyUI API adapter
        """
        self.image_repository = image_repository
        self.comfyui_adapter = comfyui_adapter
    
    async def generate_image(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        cfg: Optional[float] = None,
        seed: Optional[int] = None,
        sampler: Optional[str] = None,
        scheduler: Optional[str] = None,
        original_prompt: str = "",
        user_idea: str = "",
        ai_model: str = "",
        ai_provider: str = "",
        workflow_name: str = "anima",
        workflow_path: Optional[str] = None,
        checkpoint: Optional[str] = None
    ) -> Tuple[str, ImageMetadata]:
        """
        Generate image using ComfyUI.
        
        Args:
            positive_prompt: Final positive prompt for generation
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Sampling steps
            cfg: CFG scale
            seed: Random seed
            sampler: Sampler name
            scheduler: Scheduler name
            original_prompt: Original prompt input by user
            user_idea: Prompt modification idea input by user
            ai_model: AI model name
            ai_provider: AI provider name
            workflow_name: Workflow configuration display/file name
            workflow_path: Absolute path to the workflow JSON file to load
            checkpoint: Dynamic checkpoint model name
            
        Returns:
            Tuple[str, ImageMetadata]: (saved_path, metadata)
        """
        # Use defaults if not provided
        width = width or settings.default_image_width
        height = height or settings.default_image_height
        steps = steps or settings.default_steps
        cfg = cfg or settings.default_cfg
        seed = seed or random.randint(1, 2**32 - 1)
        sampler = sampler or settings.default_sampler
        scheduler = scheduler or settings.default_scheduler
        
        logger.info("Starting image generation", extra={
            "workflow": workflow_name,
            "width": width,
            "height": height,
            "steps": steps,
            "seed": seed,
            "checkpoint": checkpoint
        })
        
        image_data, generation_info = await self.comfyui_adapter.generate_image(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed,
            sampler=sampler,
            scheduler=scheduler,
            workflow_path=workflow_path,
            checkpoint=checkpoint
        )
        
        # Create metadata
        metadata = ImageMetadata(
            filename="",  # Will be set by repository
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed,
            sampler=sampler,
            scheduler=scheduler,
            generated_at=datetime.now(),
            original_prompt=original_prompt,
            user_idea=user_idea,
            final_prompt=positive_prompt,
            ai_model=ai_model,
            ai_provider=ai_provider,
            workflow_name=workflow_name,
            checkpoint=checkpoint or ""
        )
        
        # Save image
        saved_path = await self.image_repository.save_image(
            image_data=image_data,
            metadata=metadata
        )
        
        logger.info("Image generation completed", extra={
            "saved_path": saved_path
        })
        
        return saved_path, metadata
    
    async def get_image(self, date_str: str, filename: str) -> bytes:
        """Get image binary data by date and filename."""
        return await self.image_repository.get_image(date_str, filename)
    
    async def get_image_metadata(self, date_str: str, filename: str) -> ImageMetadata:
        """Get image metadata by date and filename."""
        return await self.image_repository.get_image_metadata(date_str, filename)
    
    async def list_images(self, date_str: str) -> list[str]:
        """List all image files for a specific date."""
        return await self.image_repository.list_images(date_str)
    
    async def get_latest_image(self, date_str: str) -> Optional[str]:
        """Get the latest image filename for a specific date."""
        return await self.image_repository.get_latest_image(date_str)

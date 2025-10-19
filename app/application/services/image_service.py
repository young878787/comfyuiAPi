"""Image service for image generation management."""

import logging
import random
from datetime import datetime

from app.domain.models import ImageMetadata
from app.infrastructure.repositories.image_repository import ImageRepository
from app.infrastructure.adapters.comfyui_adapter import ComfyUIAdapter
from app.application.services.session_service import SessionService
from app.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    """Service for managing image generation."""
    
    def __init__(
        self,
        image_repository: ImageRepository,
        comfyui_adapter: ComfyUIAdapter,
        session_service: SessionService
    ):
        """
        Initialize service with dependencies.
        
        Args:
            image_repository: Image repository
            comfyui_adapter: ComfyUI API adapter
            session_service: Session service
        """
        self.image_repository = image_repository
        self.comfyui_adapter = comfyui_adapter
        self.session_service = session_service
    
    async def generate_image(
        self,
        session_id: str,
        positive_prompt: str,
        negative_prompt: str = "",
        width: int = None,
        height: int = None,
        steps: int = None,
        cfg: float = None,
        seed: int = None,
        sampler: str = None,
        scheduler: str = None
    ) -> tuple[str, ImageMetadata]:
        """
        Generate image using ComfyUI.
        
        Args:
            session_id: Session ID
            positive_prompt: Positive prompt
            negative_prompt: Negative prompt
            width: Image width (uses default if None)
            height: Image height (uses default if None)
            steps: Sampling steps (uses default if None)
            cfg: CFG scale (uses default if None)
            seed: Random seed (generates random if None)
            sampler: Sampler name (uses default if None)
            scheduler: Scheduler name (uses default if None)
            
        Returns:
            tuple: (filename, metadata)
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
            "session_id": session_id,
            "width": width,
            "height": height,
            "steps": steps,
            "seed": seed
        })
        
        # Generate image
        image_data, generation_info = await self.comfyui_adapter.generate_image(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed,
            sampler=sampler,
            scheduler=scheduler
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
            generated_at=datetime.now()
        )
        
        # Save image
        filename = await self.image_repository.save_image(
            session_id=session_id,
            image_data=image_data,
            metadata=metadata
        )
        
        # Update image count
        await self.session_service.increment_image_count(session_id)
        
        logger.info("Image generation completed", extra={
            "session_id": session_id,
            "image_filename": filename  # 改名避免與 logging 的 filename 衝突
        })
        
        return filename, metadata
    
    async def get_image(self, session_id: str, filename: str) -> bytes:
        """
        Get image data.
        
        Args:
            session_id: Session ID
            filename: Image filename
            
        Returns:
            bytes: Image data
        """
        return await self.image_repository.get_image(session_id, filename)
    
    async def get_image_metadata(
        self,
        session_id: str,
        filename: str
    ) -> ImageMetadata:
        """
        Get image metadata.
        
        Args:
            session_id: Session ID
            filename: Image filename
            
        Returns:
            ImageMetadata: Image metadata
        """
        return await self.image_repository.get_image_metadata(session_id, filename)
    
    async def list_images(self, session_id: str) -> list[str]:
        """
        List all images for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            list: List of image filenames
        """
        return await self.image_repository.list_images(session_id)
    
    async def get_latest_image(self, session_id: str) -> str | None:
        """
        Get the latest image filename.
        
        Args:
            session_id: Session ID
            
        Returns:
            str | None: Latest image filename or None
        """
        return await self.image_repository.get_latest_image(session_id)

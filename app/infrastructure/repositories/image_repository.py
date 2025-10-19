"""Image repository for image storage."""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.domain.models import ImageMetadata
from app.domain.exceptions import SessionNotFoundError, ImageNotFoundError

logger = logging.getLogger(__name__)


class ImageRepository:
    """Repository for managing image storage."""
    
    def __init__(self):
        """Initialize repository with storage path."""
        self.storage_path = settings.sessions_path
    
    def _get_images_path(self, session_id: str) -> Path:
        """Get images directory path for session."""
        return self.storage_path / session_id / "images"
    
    def _get_next_image_number(self, session_id: str) -> int:
        """Get next available image number."""
        images_path = self._get_images_path(session_id)
        
        if not images_path.exists():
            return 1
        
        existing_images = list(images_path.glob("img_*.png"))
        
        if not existing_images:
            return 1
        
        numbers = []
        for img in existing_images:
            try:
                # Extract number from img_001.png
                num_str = img.stem.split('_')[1]
                numbers.append(int(num_str))
            except (IndexError, ValueError):
                continue
        
        return max(numbers) + 1 if numbers else 1
    
    async def save_image(
        self,
        session_id: str,
        image_data: bytes,
        metadata: ImageMetadata
    ) -> str:
        """
        Save image and its metadata.
        
        Args:
            session_id: Session ID
            image_data: Image binary data
            metadata: Image metadata
            
        Returns:
            str: Image filename
            
        Raises:
            SessionNotFoundError: If session not found
        """
        images_path = self._get_images_path(session_id)
        
        if not images_path.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        try:
            # Generate filename
            img_number = self._get_next_image_number(session_id)
            filename = f"img_{img_number:03d}.png"
            
            # Save image
            image_path = images_path / filename
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Update metadata filename
            metadata.filename = filename
            metadata.generated_at = datetime.now()
            
            # Save metadata
            metadata_path = images_path / f"img_{img_number:03d}_meta.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info("Image saved", extra={
                "session_id": session_id,
                "image_file": filename,
                "image_bytes": len(image_data)
            })
            
            return filename
            
        except Exception as e:
            logger.error("Failed to save image", extra={
                "session_id": session_id,
                "error": str(e)
            }, exc_info=True)
            raise
    
    async def get_image(self, session_id: str, filename: str) -> bytes:
        """
        Get image data.
        
        Args:
            session_id: Session ID
            filename: Image filename
            
        Returns:
            bytes: Image binary data
            
        Raises:
            ImageNotFoundError: If image not found
        """
        image_path = self._get_images_path(session_id) / filename
        
        if not image_path.exists():
            raise ImageNotFoundError(f"Image not found: {filename}")
        
        try:
            with open(image_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to read image", extra={
                "session_id": session_id,
                "filename": filename,
                "error": str(e)
            }, exc_info=True)
            raise
    
    async def get_image_metadata(
        self,
        session_id: str,
        filename: str
    ) -> Optional[ImageMetadata]:
        """
        Get image metadata.
        
        Args:
            session_id: Session ID
            filename: Image filename
            
        Returns:
            ImageMetadata: Image metadata or None if not found
        """
        # Extract base filename without extension
        base_name = filename.rsplit('.', 1)[0]
        metadata_path = self._get_images_path(session_id) / f"{base_name}_meta.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ImageMetadata.from_dict(data)
        except Exception as e:
            logger.warning("Failed to read metadata", extra={
                "session_id": session_id,
                "filename": filename,
                "error": str(e)
            })
            return None
    
    async def list_images(self, session_id: str) -> List[str]:
        """
        List all images for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[str]: List of image filenames, sorted by name
            
        Raises:
            SessionNotFoundError: If session not found
        """
        images_path = self._get_images_path(session_id)
        
        if not images_path.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        try:
            image_files = sorted(images_path.glob("img_*.png"))
            return [img.name for img in image_files]
        except Exception as e:
            logger.error("Failed to list images", extra={
                "session_id": session_id,
                "error": str(e)
            }, exc_info=True)
            raise
    
    async def get_latest_image(self, session_id: str) -> Optional[str]:
        """
        Get the latest image filename.
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[str]: Latest image filename or None if no images
        """
        images = await self.list_images(session_id)
        return images[-1] if images else None
    
    async def delete_image(self, session_id: str, filename: str) -> None:
        """
        Delete image and its metadata.
        
        Args:
            session_id: Session ID
            filename: Image filename
            
        Raises:
            ImageNotFoundError: If image not found
        """
        image_path = self._get_images_path(session_id) / filename
        
        if not image_path.exists():
            raise ImageNotFoundError(f"Image not found: {filename}")
        
        try:
            # Delete image
            image_path.unlink()
            
            # Delete metadata if exists
            base_name = filename.rsplit('.', 1)[0]
            metadata_path = image_path.parent / f"{base_name}_meta.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info("Image deleted", extra={
                "session_id": session_id,
                "filename": filename
            })
            
        except Exception as e:
            logger.error("Failed to delete image", extra={
                "session_id": session_id,
                "filename": filename,
                "error": str(e)
            }, exc_info=True)
            raise

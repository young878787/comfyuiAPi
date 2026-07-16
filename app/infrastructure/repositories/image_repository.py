"""Image repository for image storage."""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.domain.models import ImageMetadata
from app.domain.exceptions import ImageNotFoundError

logger = logging.getLogger(__name__)


class ImageRepository:
    """Repository for managing image storage."""

    def __init__(self):
        """Initialize repository with storage path."""
        # Config may not be fully refactored yet, so fall back to default outputs path
        try:
            self.storage_path = Path(settings.outputs_dir)
        except AttributeError:
            self.storage_path = Path("./outputs")

    def _get_date_path(self, date_str: str) -> Path:
        """Get directory path for a specific date."""
        path = self.storage_path / date_str
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_image_path(self, date_str: str, filename: str) -> Path:
        """Get absolute path of an image file."""
        return self.storage_path / date_str / filename

    def _get_next_image_number(self, date_str: str) -> int:
        """Get next available image number (sequence)."""
        date_path = self._get_date_path(date_str)
        existing_images = list(date_path.glob("[0-9][0-9][0-9].png"))

        if not existing_images:
            return 1

        numbers = []
        for img in existing_images:
            try:
                # Extract number from 001.png
                num_str = img.stem
                numbers.append(int(num_str))
            except ValueError:
                continue

        return max(numbers) + 1 if numbers else 1

    def save_text_record(self, filepath: Path, metadata: ImageMetadata) -> None:
        """Generate and save a human-readable text configuration summary."""
        orig_prompt = metadata.original_prompt.strip() if metadata.original_prompt else "自由發揮"
        idea = metadata.user_idea.strip() if metadata.user_idea else "直接使用原始提示詞"

        record_content = f"""================================================================================
ComfyUI 圖片生成參數記錄
================================================================================

📁 圖片檔名: {metadata.filename}
⏰ 生成時間: {metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S")}

👤 用戶原始 Prompt
--------------------------------------------------------------------------------
{orig_prompt}

💡 用戶修改想法 (Idea)
--------------------------------------------------------------------------------
{idea}

🎨 生成參數
--------------------------------------------------------------------------------
📝 最終使用 Prompt:
{metadata.positive_prompt}

🌱 Seed: {metadata.seed}
📐 解析度: {metadata.width}x{metadata.height}
⚙️  Steps: {metadata.steps}
🎯 Sampler: {metadata.sampler}
📅 Scheduler: {metadata.scheduler}
🔧 CFG: {metadata.cfg}
🖼️  Workflow: {metadata.workflow_name}

🤖 AI 修改資訊
--------------------------------------------------------------------------------
模型: {metadata.ai_model if metadata.ai_model else "無"}
提供商: {metadata.ai_provider if metadata.ai_provider else "無"}

================================================================================
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(record_content)

    async def save_image(self, image_data: bytes, metadata: ImageMetadata, date_str: Optional[str] = None) -> str:
        """
        Save image, metadata, and text log.

        Args:
            image_data: Image binary data
            metadata: Image metadata
            date_str: Folder date key (YYYY-MM-DD), defaults to today

        Returns:
            str: Relative saved path of image from root (e.g., outputs/2026-07-06/001.png)
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        date_path = self._get_date_path(date_str)

        try:
            # Generate sequence filename
            img_number = self._get_next_image_number(date_str)
            base_name = f"{img_number:03d}"
            filename = f"{base_name}.png"

            # Save image file
            image_path = date_path / filename
            with open(image_path, "wb") as f:
                f.write(image_data)

            # Update metadata attributes
            metadata.filename = filename
            metadata.generated_at = datetime.now()

            # Save structured JSON metadata
            metadata_path = date_path / f"{base_name}_meta.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

            # Save human-readable summary record
            text_path = date_path / f"{base_name}.txt"
            self.save_text_record(text_path, metadata)

            logger.info(
                "Image saved successfully", extra={"date": date_str, "file_name": filename, "bytes": len(image_data)}
            )

            return f"outputs/{date_str}/{filename}"

        except Exception as e:
            logger.error("Failed to save image", extra={"date": date_str, "error": str(e)}, exc_info=True)
            raise

    async def get_image(self, date_str: str, filename: str) -> bytes:
        """
        Get image data.

        Args:
            date_str: Date folder name
            filename: Image filename

        Returns:
            bytes: Image binary data

        Raises:
            ImageNotFoundError: If image not found
        """
        image_path = self.storage_path / date_str / filename

        if not image_path.exists():
            raise ImageNotFoundError(f"Image not found: {date_str}/{filename}")

        try:
            with open(image_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(
                "Failed to read image", extra={"date": date_str, "file_name": filename, "error": str(e)}, exc_info=True
            )
            raise

    async def get_image_metadata(self, date_str: str, filename: str) -> Optional[ImageMetadata]:
        """
        Get image metadata.

        Args:
            date_str: Date folder name
            filename: Image filename

        Returns:
            ImageMetadata: Image metadata or None if not found
        """
        base_name = filename.rsplit(".", 1)[0]
        metadata_path = self.storage_path / date_str / f"{base_name}_meta.json"

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ImageMetadata.from_dict(data)
        except Exception as e:
            logger.warning("Failed to read metadata", extra={"date": date_str, "file_name": filename, "error": str(e)})
            return None

    async def list_images(self, date_str: str) -> List[str]:
        """
        List all image filenames for a specific date.

        Args:
            date_str: Date folder name

        Returns:
            List[str]: List of image filenames, sorted by name
        """
        date_path = self.storage_path / date_str

        if not date_path.exists():
            return []

        try:
            image_files = sorted(date_path.glob("[0-9][0-9][0-9].png"))
            return [img.name for img in image_files]
        except Exception as e:
            logger.error("Failed to list images", extra={"date": date_str, "error": str(e)}, exc_info=True)
            raise

    async def get_latest_image(self, date_str: str) -> Optional[str]:
        """
        Get the latest image filename for a specific date.

        Args:
            date_str: Date folder name

        Returns:
            Optional[str]: Latest image filename or None if no images
        """
        images = await self.list_images(date_str)
        return images[-1] if images else None

    async def delete_image(self, date_str: str, filename: str) -> None:
        """
        Delete image, metadata, and text logs.

        Args:
            date_str: Date folder name
            filename: Image filename

        Raises:
            ImageNotFoundError: If image not found
        """
        image_path = self.storage_path / date_str / filename

        if not image_path.exists():
            raise ImageNotFoundError(f"Image not found: {date_str}/{filename}")

        try:
            # Delete png image
            image_path.unlink()

            base_name = filename.rsplit(".", 1)[0]

            # Delete JSON metadata
            metadata_path = image_path.parent / f"{base_name}_meta.json"
            if metadata_path.exists():
                metadata_path.unlink()

            # Delete text log summary
            text_path = image_path.parent / f"{base_name}.txt"
            if text_path.exists():
                text_path.unlink()

            logger.info("Image files deleted successfully", extra={"date": date_str, "file_name": filename})

        except Exception as e:
            logger.error(
                "Failed to delete image files",
                extra={"date": date_str, "file_name": filename, "error": str(e)},
                exc_info=True,
            )
            raise

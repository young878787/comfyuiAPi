"""Image generation and management routes."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
import io
import base64
import logging

from app.application.dtos.common import (
    ImageResponse,
    ImageListResponse
)
from app.application.services.image_service import ImageService
from app.infrastructure.repositories.image_repository import ImageRepository
from app.infrastructure.adapters.comfyui_adapter import ComfyUIAdapter
from app.infrastructure.adapters.ai_adapter_factory import create_ai_adapter
from app.domain.exceptions import ImageNotFoundError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image", tags=["images"])


def get_image_service() -> ImageService:
    """Dependency to get image service."""
    image_repository = ImageRepository()
    comfyui_adapter = ComfyUIAdapter()
    return ImageService(image_repository, comfyui_adapter)


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze an uploaded image using the configured AI."""
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")
        mime_type = file.content_type or "image/jpeg"
        
        ai_adapter = create_ai_adapter()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "請詳細分析這張圖片的內容，描述你看到了什麼。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        result = await ai_adapter.generate_response(messages)
        return {"result": result}
    except Exception as e:
        logger.exception(f"Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/view/{date_str}/{filename}")
async def view_image(
    date_str: str,
    filename: str,
    service: ImageService = Depends(get_image_service)
):
    """View an image."""
    try:
        image_data = await service.get_image(date_str, filename)
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/png"
        )
    except ImageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{date_str}/{filename}")
async def download_image(
    date_str: str,
    filename: str,
    service: ImageService = Depends(get_image_service)
):
    """Download an image."""
    try:
        image_data = await service.get_image(date_str, filename)
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ImageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{date_str}", response_model=ImageListResponse)
async def list_images(
    date_str: str,
    service: ImageService = Depends(get_image_service)
):
    """List all images for a specific date."""
    try:
        images = await service.list_images(date_str)
        latest = await service.get_latest_image(date_str)
        
        return ImageListResponse(
            date=date_str,
            images=images,
            latest_image=latest
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata/{date_str}/{filename}", response_model=ImageResponse)
async def get_image_metadata(
    date_str: str,
    filename: str,
    service: ImageService = Depends(get_image_service)
):
    """Retrieve metadata of a specific image."""
    try:
        metadata = await service.get_image_metadata(date_str, filename)
        if not metadata:
            raise HTTPException(status_code=404, detail="Metadata not found")
        return ImageResponse(
            filename=filename,
            url=f"/api/image/view/{date_str}/{filename}",
            metadata=metadata.to_dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

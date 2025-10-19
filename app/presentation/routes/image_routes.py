"""Image generation and management routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
import io

from app.application.dtos.common import (
    ImageGenerateRequest,
    ImageResponse,
    ImageListResponse
)
from app.application.services.image_service import ImageService
from app.application.services.session_service import SessionService
from app.infrastructure.repositories.image_repository import ImageRepository
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.adapters.comfyui_adapter import ComfyUIAdapter
from app.domain.exceptions import SessionNotFoundError, ImageNotFoundError, ImageGenerationError
from app.config import settings

router = APIRouter(prefix="/api/image", tags=["images"])


def get_image_service() -> ImageService:
    """Dependency to get image service."""
    image_repository = ImageRepository()
    comfyui_adapter = ComfyUIAdapter()
    session_repository = SessionRepository()
    session_service = SessionService(session_repository)
    return ImageService(image_repository, comfyui_adapter, session_service)


@router.post("/generate", response_model=ImageResponse)
async def generate_image(
    request: ImageGenerateRequest,
    service: ImageService = Depends(get_image_service)
):
    """Generate an image using ComfyUI."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        filename, metadata = await service.generate_image(
            session_id=request.session_id,
            positive_prompt=request.positive_prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
            cfg=request.cfg,
            seed=request.seed,
            sampler=request.sampler,
            scheduler=request.scheduler
        )
        
        # 更新 metadata 的 filename
        metadata.filename = filename
        
        response = ImageResponse(
            filename=filename,
            url=f"/api/image/view/{request.session_id}/{filename}",
            metadata=metadata.to_dict()
        )
        
        logger.info(f"Returning response: {response}")
        return response
        
    except SessionNotFoundError as e:
        logger.error(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ImageGenerationError as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in image generation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/view/{session_id}/{filename}")
async def view_image(
    session_id: str,
    filename: str,
    service: ImageService = Depends(get_image_service)
):
    """View an image."""
    try:
        image_data = await service.get_image(session_id, filename)
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/png"
        )
    except ImageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/download/{session_id}/{filename}")
async def download_image(
    session_id: str,
    filename: str,
    service: ImageService = Depends(get_image_service)
):
    """Download an image."""
    try:
        image_data = await service.get_image(session_id, filename)
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ImageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/list/{session_id}", response_model=ImageListResponse)
async def list_images(
    session_id: str,
    service: ImageService = Depends(get_image_service)
):
    """List all images for a session."""
    try:
        images = await service.list_images(session_id)
        latest = await service.get_latest_image(session_id)
        
        return ImageListResponse(
            session_id=session_id,
            images=images,
            latest_image=latest
        )
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

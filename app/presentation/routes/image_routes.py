"""Image generation and management routes."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional
import io
import base64
import logging

from app.application.dtos.common import (
    ImageResponse,
    ImageListResponse,
    OpenFolderRequest
)
from app.application.services.image_service import ImageService
from app.application.services.metadata_parser import parse_image_metadata
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


@router.post("/parse-metadata")
async def parse_metadata(file: UploadFile = File(...)):
    """Parse Stable Diffusion and ComfyUI metadata from an uploaded image."""
    try:
        contents = await file.read()
        metadata = parse_image_metadata(contents)
        return metadata
    except Exception as e:
        logger.exception(f"Error parsing image metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        image_path = service.get_image_path(date_str, filename)
        if not image_path.exists():
            raise ImageNotFoundError(f"Image not found: {date_str}/{filename}")
        return FileResponse(
            image_path,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=31536000, immutable"}
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
        image_path = service.get_image_path(date_str, filename)
        if not image_path.exists():
            raise ImageNotFoundError(f"Image not found: {date_str}/{filename}")
        return FileResponse(
            image_path,
            media_type="image/png",
            filename=filename,
            headers={"Cache-Control": "public, max-age=31536000, immutable"}
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
        
        # Build image details list to speed up frontend loading
        images_details = []
        for filename in images:
            metadata = await service.get_image_metadata(date_str, filename)
            meta_dict = metadata.to_dict() if metadata else {}
            images_details.append(
                ImageResponse(
                    filename=filename,
                    url=f"/api/image/view/{date_str}/{filename}",
                    metadata=meta_dict
                )
            )
        
        return ImageListResponse(
            date=date_str,
            images=images,
            latest_image=latest,
            images_details=images_details
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


@router.post("/open-folder")
async def open_folder(
    request: OpenFolderRequest,
    service: ImageService = Depends(get_image_service)
):
    """Open the local folder of ComfyUI output (or fallback to local app outputs) in Windows Explorer."""
    try:
        workflow_name = request.workflow or "Anima"
        comfy_dir = settings.comfyui_output_dir
        
        target_dir = None
        target_file = None
        
        # 1. Try to locate ComfyUI output folder
        if comfy_dir:
            from pathlib import Path
            comfy_base = Path(comfy_dir)
            if comfy_base.exists():
                # Check different cases of workflow name folder
                if "放大" in workflow_name or "upscale" in workflow_name.lower():
                    wf_names = ["AnimaUpscaled"]
                else:
                    wf_names = [workflow_name, workflow_name.capitalize(), workflow_name.lower()]
                for wf in wf_names:
                    temp_dir = comfy_base / wf / request.date_str
                    if temp_dir.exists():
                        target_dir = temp_dir
                        break
                        
                # If target directory is found, try to find matching image file to highlight
                if target_dir and request.filename:
                    # Try to get comfyui_filename from local metadata first
                    comfyui_filename = None
                    try:
                        metadata = await service.get_image_metadata(request.date_str, request.filename)
                        if metadata:
                            comfyui_filename = getattr(metadata, 'comfyui_filename', None)
                    except Exception as e:
                        logger.warning(f"Error reading image metadata for open-folder: {e}")
                    
                    if comfyui_filename:
                        temp_file = target_dir / comfyui_filename
                        if temp_file.exists():
                            target_file = temp_file
                    
                    # Fallback to number index search if comfyui_filename not found or doesn't exist
                    if not target_file:
                        try:
                            stem = Path(request.filename).stem  # e.g., "001"
                            idx_num = int(stem)
                            # ComfyUI output files usually have padding numbers (e.g. Anima_00001_.png)
                            patterns = [
                                f"*{idx_num:05d}*.png",
                                f"*{idx_num:04d}*.png",
                                f"*{idx_num:03d}*.png",
                                f"*{idx_num}*.png",
                                f"*{idx_num:05d}*.webp",
                                f"*{idx_num:04d}*.webp",
                                f"*{idx_num:03d}*.webp",
                                f"*{idx_num}*.webp"
                            ]
                            for pattern in patterns:
                                matches = list(target_dir.glob(pattern))
                                if matches:
                                    target_file = matches[0]
                                    break
                        except Exception as ex:
                            logger.warning(f"Error parsing image index to locate ComfyUI file: {ex}")
                            
        # 2. Fallback to local outputs folder if ComfyUI output folder is not found/accessible
        if not target_dir or not target_dir.exists():
            from pathlib import Path
            local_base = Path(settings.outputs_dir)
            target_dir = local_base / request.date_str
            if request.filename:
                local_file = target_dir / request.filename
                if local_file.exists():
                    target_file = local_file

        # 3. Open in Windows Explorer
        import subprocess
        if target_file and target_file.exists():
            path_str = str(target_file.absolute()).replace('/', '\\')
            subprocess.Popen(f'explorer.exe /select,"{path_str}"')
            logger.info(f"Opened Explorer with selected file: {path_str}")
        elif target_dir and target_dir.exists():
            path_str = str(target_dir.absolute()).replace('/', '\\')
            subprocess.Popen(f'explorer.exe "{path_str}"')
            logger.info(f"Opened Explorer folder: {path_str}")
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Neither ComfyUI folder nor local fallback directory could be found for date {request.date_str}."
            )
            
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to open folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{date_str}/{filename}")
async def delete_image(
    date_str: str,
    filename: str,
    service: ImageService = Depends(get_image_service)
):
    """Delete an image and its corresponding metadata/logs."""
    try:
        await service.image_repository.delete_image(date_str, filename)
        return {"success": True, "message": f"Image {filename} deleted successfully"}
    except ImageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to delete image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


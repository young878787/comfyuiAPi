"""FastAPI routes for generation SSE pipeline."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.application.dtos.common import GenerateRequest
from app.application.services.generate_service import GenerateService
from app.application.services.image_service import ImageService
from app.infrastructure.repositories.image_repository import ImageRepository
from app.infrastructure.adapters.comfyui_adapter import ComfyUIAdapter

router = APIRouter(prefix="/api", tags=["generate"])


def get_generate_service() -> GenerateService:
    """Dependency injection helper for GenerateService."""
    image_repo = ImageRepository()
    comfyui_adapter = ComfyUIAdapter()
    image_service = ImageService(image_repo, comfyui_adapter)
    return GenerateService(image_service)


@router.post("/generate")
async def generate(request: GenerateRequest, service: GenerateService = Depends(get_generate_service)):
    """
    Handle POST generate request and stream SSE progress events.
    """
    generator = service.generate(request)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )

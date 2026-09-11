"""AI model catalog and runtime selection routes."""

import logging

from fastapi import APIRouter, HTTPException, Response

from app.application.dtos.common import ModelCatalogResponse, ModelInfo, ModelSelectRequest
from app.application.services.model_catalog_service import ModelCatalogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai-models"])


@router.get("/models", response_model=ModelCatalogResponse)
async def list_models(response: Response):
    """Get the available model list (cache-first) and the current model."""
    response.headers["Cache-Control"] = "no-store"
    service = ModelCatalogService()
    catalog = await service.get_models()
    return ModelCatalogResponse(
        fetched_at=int(catalog.get("fetched_at", 0)),
        source=str(catalog.get("source", "")),
        stale=bool(catalog.get("stale", False)),
        models=[ModelInfo(**m) for m in catalog.get("models", [])],
        current_model=service.get_current_model(),
    )


@router.post("/models/refresh", response_model=ModelCatalogResponse)
async def refresh_models():
    """Force-refresh the model list from the provider API."""
    service = ModelCatalogService()
    catalog = await service.get_models(force_refresh=True)
    return ModelCatalogResponse(
        fetched_at=int(catalog.get("fetched_at", 0)),
        source=str(catalog.get("source", "")),
        stale=bool(catalog.get("stale", False)),
        models=[ModelInfo(**m) for m in catalog.get("models", [])],
        current_model=service.get_current_model(),
    )


@router.get("/models/current")
async def current_model():
    """Get the currently active model ID."""
    service = ModelCatalogService()
    return {"current_model": service.get_current_model()}


@router.post("/models/current", response_model=ModelCatalogResponse)
async def select_model(body: ModelSelectRequest):
    """Switch the active AI model at runtime and persist the choice."""
    service = ModelCatalogService()

    # Validate against the catalog when it is reachable
    catalog = await service.get_models()
    available_ids = [m.get("id") for m in catalog.get("models", [])]
    if available_ids and body.model_id not in available_ids:
        raise HTTPException(status_code=400, detail=f"Unknown model '{body.model_id}'. Available: {available_ids}")

    try:
        current = service.set_current_model(body.model_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ModelCatalogResponse(
        fetched_at=int(catalog.get("fetched_at", 0)),
        source=str(catalog.get("source", "")),
        stale=bool(catalog.get("stale", False)),
        models=[ModelInfo(**m) for m in catalog.get("models", [])],
        current_model=current,
    )

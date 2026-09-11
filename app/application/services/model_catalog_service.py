"""AI model catalog service.

Fetches the available model list from the OpenCode Go models API,
caches it to disk (survives restarts), and manages the runtime-selected
model ID persisted in a runtime config file.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.domain.exceptions import APIError

logger = logging.getLogger(__name__)


class ModelCatalogService:
    """Manage the AI model list cache and the runtime-selected model."""

    # Class-level cache so the adapter can resolve the model cheaply per request
    _current_model: Optional[str] = None

    def __init__(self) -> None:
        self.cache_file = Path(settings.ai_models_cache_file)
        self.runtime_file = Path(settings.runtime_config_file)
        self.ttl_seconds = max(settings.ai_models_cache_ttl_hours, 0) * 3600

    # ------------------------------------------------------------------
    # Model list (catalog)
    # ------------------------------------------------------------------
    async def fetch_remote_models(self) -> List[Dict[str, Any]]:
        """Call the provider models API and return a normalized model list."""
        headers = {}
        if settings.opencode_api_key:
            headers["Authorization"] = f"Bearer {settings.opencode_api_key}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(settings.opencode_models_url, headers=headers)
            response.raise_for_status()
            data = response.json()

        raw_models = data.get("data") if isinstance(data, dict) else None
        if not isinstance(raw_models, list):
            raise APIError("Models API returned unexpected response shape")

        models: List[Dict[str, Any]] = []
        for item in raw_models:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            models.append(
                {
                    "id": str(item["id"]),
                    "owned_by": str(item.get("owned_by") or ""),
                    "created": item.get("created"),
                }
            )
        models.sort(key=lambda m: m["id"])
        return models

    async def get_models(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get the model catalog.

        Priority: fresh cache -> remote API -> stale cache -> minimal fallback.
        Always writes a successful remote fetch back to the cache file.
        """
        cache = self._read_cache()

        if not force_refresh and cache and not self._is_expired(cache):
            return cache

        try:
            models = await self.fetch_remote_models()
            payload = {
                "fetched_at": int(time.time()),
                "source": settings.opencode_models_url,
                "stale": False,
                "models": models,
            }
            self._write_cache(payload)
            logger.info("AI model catalog updated", extra={"model_count": len(models)})
            return payload
        except Exception as exc:
            if cache:
                logger.warning("Model catalog refresh failed, using stale cache: %s", exc)
                stale = dict(cache)
                stale["stale"] = True
                return stale

            logger.warning("Model catalog refresh failed with no cache, using fallback: %s", exc)
            fallback = {
                "fetched_at": int(time.time()),
                "source": "fallback",
                "stale": True,
                "models": [
                    {"id": settings.opencode_model, "owned_by": "fallback", "created": None}
                ],
            }
            return fallback

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        try:
            if self.cache_file.exists():
                data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("models"), list):
                    return data
        except Exception as exc:
            logger.warning("Failed to read model catalog cache: %s", exc)
        return None

    def _write_cache(self, payload: Dict[str, Any]) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            logger.warning("Failed to write model catalog cache: %s", exc)

    def _is_expired(self, cache: Dict[str, Any]) -> bool:
        if self.ttl_seconds <= 0:
            return False
        fetched_at = cache.get("fetched_at")
        if not isinstance(fetched_at, (int, float)):
            return True
        return (time.time() - fetched_at) > self.ttl_seconds

    # ------------------------------------------------------------------
    # Runtime-selected model
    # ------------------------------------------------------------------
    def get_current_model(self) -> str:
        """Get the active model ID (runtime override -> .env default)."""
        if ModelCatalogService._current_model is None:
            ModelCatalogService._current_model = self._load_persisted_model() or settings.opencode_model
        return ModelCatalogService._current_model

    def set_current_model(self, model_id: str) -> str:
        """Switch the active model and persist it for future restarts."""
        model_id = (model_id or "").strip()
        if not model_id:
            raise ValueError("model_id is required")

        ModelCatalogService._current_model = model_id

        try:
            self.runtime_file.parent.mkdir(parents=True, exist_ok=True)
            self.runtime_file.write_text(
                json.dumps(
                    {
                        "current_model": model_id,
                        "provider": settings.ai_provider,
                        "updated_at": int(time.time()),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Failed to persist runtime model selection: %s", exc)

        logger.info("AI model switched", extra={"current_model": model_id})
        return model_id

    def _load_persisted_model(self) -> Optional[str]:
        try:
            if self.runtime_file.exists():
                data = json.loads(self.runtime_file.read_text(encoding="utf-8"))
                model = data.get("current_model")
                if isinstance(model, str) and model.strip():
                    return model.strip()
        except Exception as exc:
            logger.warning("Failed to load runtime model selection: %s", exc)
        return None

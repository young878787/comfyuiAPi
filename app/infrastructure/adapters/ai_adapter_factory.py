"""Factory for creating the active AI provider adapter."""

import logging

from app.config import settings
from app.infrastructure.adapters.base_ai_adapter import BaseAIAdapter
from app.infrastructure.adapters.github_model_adapter import GitHubModelAdapter
from app.infrastructure.adapters.google_ai_adapter import GoogleAIAdapter

logger = logging.getLogger(__name__)


def create_ai_adapter() -> BaseAIAdapter:
    """
    Create and return the AI adapter for the configured provider.

    Reads AI_PROVIDER from settings:
      "github" -> GitHubModelAdapter
      "google" -> GoogleAIAdapter

    Returns:
        BaseAIAdapter: The active AI adapter instance

    Raises:
        ValueError: If AI_PROVIDER is not recognised
    """
    provider = settings.ai_provider.lower().strip()

    if provider == "github":
        logger.info("AI provider: GitHub Models (%s)", settings.github_model)
        return GitHubModelAdapter()

    if provider == "google":
        logger.info("AI provider: Google AI Studio (%s)", settings.google_model)
        return GoogleAIAdapter()

    raise ValueError(
        f"Unknown AI_PROVIDER '{settings.ai_provider}'. "
        "Valid options: github, google"
    )

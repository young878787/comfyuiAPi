"""Google AI Studio adapter (OpenAI-compatible endpoint)."""

import httpx
import logging
from typing import List, Dict, Any

from app.config import settings
from app.domain.exceptions import APIError
from app.infrastructure.adapters.base_ai_adapter import BaseAIAdapter

logger = logging.getLogger(__name__)


class GoogleAIAdapter(BaseAIAdapter):
    """
    Adapter for Google AI Studio using its OpenAI-compatible endpoint.

    Compatible models (set GOOGLE_MODEL in .env):
      gemma-4-27b-it, gemma-3-27b-it, gemma-3-12b-it, gemini-2.0-flash, ...
    """

    def __init__(self):
        """Initialize the adapter with configuration."""
        self.api_url = settings.google_api_url
        self.api_key = settings.google_api_key
        self.model = settings.google_model
        self.timeout = 60.0

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate AI response using Google AI Studio (OpenAI-compatible format).

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            str: AI-generated response content

        Raises:
            APIError: If the API call fails
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(
                    "Calling Google AI Studio API",
                    extra={"model": self.model, "message_count": len(messages)},
                )

                response = await client.post(
                    self.api_url, headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]

                logger.info(
                    "Google AI Studio API call successful",
                    extra={"response_length": len(content)},
                )

                return content

        except httpx.HTTPStatusError as e:
            logger.error(
                "Google AI Studio API HTTP error",
                extra={"status_code": e.response.status_code, "error": str(e)},
                exc_info=True,
            )
            raise APIError(
                f"Google AI Studio API error: {e.response.status_code} - {e.response.text}"
            )

        except httpx.TimeoutException:
            logger.error("Google AI Studio API timeout")
            raise APIError("Google AI Studio API timeout")

        except Exception as e:
            logger.error(
                "Google AI Studio API unexpected error",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise APIError(f"Google AI Studio API error: {str(e)}")

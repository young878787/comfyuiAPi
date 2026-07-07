"""OpenCode API adapter."""

import httpx
import logging
from typing import List, Dict, Any

from app.config import settings
from app.domain.exceptions import APIError
from app.infrastructure.adapters.base_ai_adapter import BaseAIAdapter
from app.infrastructure.retry_utils import retry_async

logger = logging.getLogger(__name__)


class OpenCodeAdapter(BaseAIAdapter):
    """Adapter for OpenCode API."""

    def __init__(self):
        """Initialize the adapter with configuration."""
        self.api_url = settings.opencode_api_url
        self.api_key = settings.opencode_api_key
        self.model = settings.opencode_model
        self.thinking = settings.opencode_thinking
        self.timeout = 180.0

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate AI response using OpenCode API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            str: AI generated response content

        Raises:
            APIError: If API call fails
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Handle the thinking field from sample
        if self.thinking:
            payload["thinking"] = {"type": self.thinking}

        async def _do_generate():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                try:
                    choice = data["choices"][0]
                    message = choice["message"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise APIError("OpenCode returned unexpected response shape") from exc
                
                # Check for content, and handle fallback logic similar to the sample
                content = message.get("content")
                if content and str(content).strip():
                    return str(content)
                
                # Fallback to reasoning_content
                reasoning_content = message.get("reasoning_content")
                if reasoning_content and str(reasoning_content).strip():
                    return str(reasoning_content)
                
                # Fallback to reasoning
                reasoning = message.get("reasoning")
                if reasoning:
                    if isinstance(reasoning, str) and reasoning.strip():
                        return reasoning
                    elif not isinstance(reasoning, str):
                        import json
                        reasoning_str = json.dumps(reasoning, ensure_ascii=False)
                        if reasoning_str.strip():
                            return reasoning_str

                if content is not None:
                    return str(content)
                raise APIError("OpenCode response content is empty")

        try:
            logger.info("Calling OpenCode API", extra={
                "model": self.model,
                "message_count": len(messages)
            })

            content = await retry_async(_do_generate, max_retries=3, delay=1.0, backoff=2.0)

            logger.info("OpenCode API call successful", extra={
                "response_length": len(content)
            })

            return content

        except httpx.HTTPStatusError as e:
            logger.error("OpenCode API HTTP error", extra={
                "status_code": e.response.status_code,
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"OpenCode API error: {e.response.status_code}")

        except httpx.TimeoutException:
            logger.error("OpenCode API timeout")
            raise APIError("OpenCode API timeout")

        except Exception as e:
            if isinstance(e, APIError):
                raise
            logger.error("OpenCode API unexpected error", extra={
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"OpenCode API error: {str(e)}")

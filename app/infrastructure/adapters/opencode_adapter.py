"""OpenCode API adapter.

Supports the OpenCode Go plan model families across three endpoint styles:
- chat/completions (OpenAI-compatible): glm, kimi, deepseek, longcat, mimo, hy ...
- messages (Anthropic-compatible): minimax, qwen
- responses (OpenAI Responses): grok, gpt, muse-spark, omen

The model ID is resolved per request so runtime model switching works
without recreating the adapter.
"""

import httpx
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.domain.exceptions import APIError
from app.infrastructure.adapters.base_ai_adapter import BaseAIAdapter
from app.infrastructure.retry_utils import retry_async

logger = logging.getLogger(__name__)

# OpenCode Go requires a stable x-opencode-session ID per conversation.
# Fall back to one ID per process when OPENCODE_SESSION_ID is not configured.
_DEFAULT_SESSION_ID = uuid.uuid4().hex

# Model families that accept the "thinking" parameter on OpenCode Go.
# Models outside these families get the parameter omitted entirely;
# if the server still rejects it, we retry once without thinking.
_THINKING_MODEL_PREFIXES: Tuple[str, ...] = ("glm", "deepseek", "kimi")

# Model families grouped by endpoint style on the Go plan
_RESPONSES_MODEL_PREFIXES: Tuple[str, ...] = ("grok", "gpt-", "muse-spark", "omen")
_MESSAGES_MODEL_PREFIXES: Tuple[str, ...] = ("minimax", "qwen")

_THING_PARAM_ERROR_KEYWORDS: Tuple[str, ...] = ("thinking", "unknown parameter", "unrecognized", "unsupported parameter")


def resolve_endpoint_style(model_id: str) -> str:
    """Resolve the endpoint style ('responses' | 'messages' | 'chat') for a model."""
    lowered = model_id.lower()
    if lowered.startswith(_RESPONSES_MODEL_PREFIXES):
        return "responses"
    if lowered.startswith(_MESSAGES_MODEL_PREFIXES):
        return "messages"
    return "chat"


class OpenCodeAdapter(BaseAIAdapter):
    """Adapter for OpenCode API."""

    def __init__(self):
        """Initialize the adapter with configuration."""
        self.api_url = settings.opencode_api_url
        self.api_key = settings.opencode_api_key
        self.default_model = settings.opencode_model
        self.thinking = settings.opencode_thinking
        self.session_id = settings.opencode_session_id.strip() or _DEFAULT_SESSION_ID
        self.timeout = 180.0

    # ------------------------------------------------------------------
    # Dynamic properties (resolved per request so runtime switching works)
    # ------------------------------------------------------------------
    @property
    def model(self) -> str:
        """Current model ID, read from runtime state with .env fallback."""
        try:
            from app.application.services.model_catalog_service import ModelCatalogService

            current = ModelCatalogService().get_current_model()
            return current or self.default_model
        except Exception:
            return self.default_model

    @property
    def endpoint_style(self) -> str:
        return resolve_endpoint_style(self.model)

    @property
    def endpoint_url(self) -> str:
        """Resolve the endpoint URL for the current model."""
        if self.endpoint_style == "chat":
            return self.api_url
        base = self.api_url.rsplit("/chat/completions", 1)[0].rstrip("/")
        return f"{base}/{self.endpoint_style}"

    @property
    def _thinking_supported(self) -> bool:
        return self.model.lower().startswith(_THINKING_MODEL_PREFIXES)

    # ------------------------------------------------------------------
    # Payload builders per endpoint style
    # ------------------------------------------------------------------
    def _build_payload(self, messages: List[Dict[str, Any]], temperature: float, max_tokens: int) -> Dict[str, Any]:
        style = self.endpoint_style

        if style == "chat":
            payload: Dict[str, Any] = {
                "messages": messages,
                "model": self.model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if self.thinking and self._thinking_supported:
                payload["thinking"] = {"type": self.thinking}
            return payload

        if style == "messages":
            system_lines = [str(m.get("content") or "") for m in messages if m.get("role") == "system"]
            rest = [m for m in messages if m.get("role") != "system"]
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": rest,
            }
            if system_lines:
                payload["system"] = "\n".join(system_lines)
            if self.thinking and self._thinking_supported:
                payload["thinking"] = {"type": self.thinking}
            return payload

        # responses
        payload = {
            "model": self.model,
            "input": messages,
            "max_output_tokens": max_tokens,
        }
        return payload

    @staticmethod
    def _strip_thinking(payload: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = dict(payload)
        cleaned.pop("thinking", None)
        return cleaned

    # ------------------------------------------------------------------
    # Response parsing per endpoint style
    # ------------------------------------------------------------------
    def _parse_content(self, data: Dict[str, Any]) -> str:
        style = self.endpoint_style

        if style == "responses":
            error = data.get("error")
            if isinstance(error, dict) and error.get("message"):
                raise APIError(f"OpenCode Responses error: {error.get('message')}")

            output = data.get("output")
            if isinstance(output, list):
                texts: List[str] = []
                for item in output:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "message":
                        content = item.get("content")
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and str(block.get("type", "")).endswith("text"):
                                    text = block.get("text")
                                    if isinstance(text, str) and text.strip():
                                        texts.append(text)
                        elif isinstance(content, str) and content.strip():
                            texts.append(content)
                if texts:
                    return "\n".join(texts)

            incomplete = data.get("incomplete_details") or {}
            if data.get("status") == "incomplete" and incomplete.get("reason") == "max_output_tokens":
                raise APIError(
                    "OpenCode Responses incomplete: max_output_tokens too small for this reasoning model"
                )

            # Some gateways wrap Responses API in chat-completions shape
            return self._parse_chat_content(data)

        if style == "messages":
            content = data.get("content")
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                texts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                joined = "\n".join(t for t in texts if t.strip())
                if joined.strip():
                    return joined
            raise APIError("OpenCode response content is empty")

        return self._parse_chat_content(data)

    @staticmethod
    def _parse_chat_content(data: Dict[str, Any]) -> str:
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

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
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
            "Authorization": f"Bearer {self.api_key}",
            "x-opencode-session": self.session_id,
        }
        # Anthropic-compatible endpoint expects x-api-key instead of Bearer auth
        if self.endpoint_style == "messages":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"

        async def _do_generate(payload: Dict[str, Any]) -> str:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint_url, headers=headers, json=payload)
                if response.status_code >= 400:
                    body = (response.text or "")[:500]
                    raise APIError(f"OpenCode API error: {response.status_code} {body}")
                data = response.json()
            return self._parse_content(data)

        payload = self._build_payload(messages, temperature, max_tokens)

        try:
            logger.info(
                "Calling OpenCode API model=%s endpoint=%s messages=%d",
                self.model,
                self.endpoint_url,
                len(messages),
            )

            content = await retry_async(lambda: _do_generate(payload), max_retries=3, delay=1.0, backoff=2.0)

            logger.info("OpenCode API call successful", extra={"response_length": len(content)})

            return content

        except APIError as e:
            # Some models do not accept the thinking parameter: retry once without it
            if "thinking" in payload and any(
                keyword in str(e).lower() for keyword in _THING_PARAM_ERROR_KEYWORDS
            ):
                logger.warning(
                    "Model may not support the thinking parameter, retrying without it",
                    extra={"model": self.model},
                )
                cleaned = self._strip_thinking(payload)
                try:
                    content = await retry_async(lambda: _do_generate(cleaned), max_retries=3, delay=1.0, backoff=2.0)
                    logger.info("OpenCode API call successful (without thinking)", extra={"response_length": len(content)})
                    return content
                except Exception as retry_exc:
                    raise self._wrap_error(retry_exc)
            raise self._wrap_error(e)

        except Exception as e:
            raise self._wrap_error(e)

    @staticmethod
    def _wrap_error(e: Exception) -> APIError:
        if isinstance(e, APIError):
            return e

        if isinstance(e, httpx.TimeoutException):
            logger.error("OpenCode API timeout")
            return APIError("OpenCode API timeout")

        if isinstance(e, httpx.HTTPStatusError):
            logger.error(
                "OpenCode API HTTP error",
                extra={"status_code": e.response.status_code, "error": str(e)},
                exc_info=True,
            )
            return APIError(f"OpenCode API error: {e.response.status_code}")

        logger.error("OpenCode API unexpected error", extra={"error": str(e)}, exc_info=True)
        return APIError(f"OpenCode API error: {str(e)}")

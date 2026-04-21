"""Abstract base class for AI model adapters."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAIAdapter(ABC):
    """Common interface for all AI provider adapters."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate an AI response for the given messages.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            str: AI-generated response content

        Raises:
            APIError: If the API call fails
        """

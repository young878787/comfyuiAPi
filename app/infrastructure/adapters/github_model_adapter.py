"""GitHub Models API adapter."""

import httpx
import logging
from typing import List, Dict, Any, Optional

from app.config import settings
from app.domain.exceptions import APIError

logger = logging.getLogger(__name__)


class GitHubModelAdapter:
    """Adapter for GitHub Models API (GPT-4o)."""
    
    def __init__(self):
        """Initialize the adapter with configuration."""
        self.api_url = settings.github_api_url
        self.api_token = settings.github_api_token
        self.model = settings.github_model
        self.timeout = 60.0
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate AI response using GitHub Models API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response (defaults to settings)
            
        Returns:
            str: AI generated response content
            
        Raises:
            APIError: If API call fails
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens or settings.qwen3vl_max_tokens,  # 使用配置的預設值
            "top_p": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("Calling GitHub Models API", extra={
                    "model": self.model,
                    "message_count": len(messages)
                })
                
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract content from response
                content = data["choices"][0]["message"]["content"]
                
                logger.info("GitHub Models API call successful", extra={
                    "response_length": len(content)
                })
                
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error("GitHub Models API HTTP error", extra={
                "status_code": e.response.status_code,
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"GitHub Models API error: {e.response.status_code}")
            
        except httpx.TimeoutException:
            logger.error("GitHub Models API timeout")
            raise APIError("GitHub Models API timeout")
            
        except Exception as e:
            logger.error("GitHub Models API unexpected error", extra={
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"GitHub Models API error: {str(e)}")

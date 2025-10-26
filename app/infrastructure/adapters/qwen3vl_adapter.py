"""Qwen3VL API adapter - 調用本地 Qwen3VL 服務"""

import httpx
import logging
from typing import List, Dict, Optional
from pathlib import Path

from app.config import settings
from app.domain.exceptions import APIError
from app.domain.utils.qwen3_filter import clean_qwen3_response

logger = logging.getLogger(__name__)


class Qwen3VLAdapter:
    """
    Qwen3VL API 適配器
    
    調用本地 Qwen3VL 服務 (Port 8001)
    每次傳送完整的組合提示詞，確保模型狀態乾淨
    """
    
    def __init__(self):
        """Initialize the adapter with configuration."""
        self.api_url = settings.qwen3vl_api_url
        self.timeout = 1200.0  # 本地推理可能需要較長時間
        self.model_name = "Qwen3-VL-4B-Thinking"
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> tuple[str, str, int, float]:
        """
        生成 AI 回應（純文字）
        
        Args:
            messages: 訊息列表，格式: [{"role": "system/user/assistant", "content": "..."}]
            temperature: 採樣溫度
            max_tokens: 最大生成 token 數
            
        Returns:
            tuple: (cleaned_content, raw_content, tokens_generated, generation_time)
                - cleaned_content: 清理後的回應內容
                - raw_content: 原始模型輸出
                - tokens_generated: 生成的 token 數
                - generation_time: 生成耗時（秒）
            
        Raises:
            APIError: 如果 API 調用失敗
        """
        # 組合完整提示詞（包含上下文）
        prompt = self._build_complete_prompt(messages)
        
        payload = {
            "prompt": prompt,
            "temperature": temperature or settings.qwen3vl_temperature,
            "max_tokens": max_tokens or settings.qwen3vl_max_tokens,
            "top_p": 0.9
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("Calling Qwen3VL API", extra={
                    "endpoint": "/generate",
                    "prompt_length": len(prompt)
                })
                
                response = await client.post(
                    f"{self.api_url}/generate",
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                content = data["content"]
                tokens = data.get("tokens_generated", 0)
                gen_time = data.get("generation_time", 0)
                
                # 清理 Qwen3 特殊標籤 (例如 <think>...</think>)
                cleaned_content = clean_qwen3_response(content, debug=True)
                
                logger.info("Qwen3VL API call successful", extra={
                    "response_length": len(content),
                    "cleaned_length": len(cleaned_content),
                    "tokens_generated": tokens,
                    "generation_time": f"{gen_time:.2f}s"
                })
                
                return cleaned_content, content, tokens, gen_time
                
        except httpx.HTTPStatusError as e:
            logger.error("Qwen3VL API HTTP error", extra={
                "status_code": e.response.status_code,
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"Qwen3VL API error: {e.response.status_code}")
            
        except httpx.TimeoutException:
            logger.error("Qwen3VL API timeout")
            raise APIError("Qwen3VL API timeout - model inference took too long")
            
        except Exception as e:
            logger.error("Qwen3VL API unexpected error", extra={
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"Qwen3VL API error: {str(e)}")
    
    async def generate_with_image(
        self,
        messages: List[Dict[str, str]],
        image_path: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> tuple[str, str, int, float]:
        """
        生成 AI 回應（圖片 + 文字）
        
        Args:
            messages: 訊息列表
            image_path: 圖片檔案路徑
            temperature: 採樣溫度
            max_tokens: 最大生成 token 數
            
        Returns:
            tuple: (cleaned_content, raw_content, tokens_generated, generation_time)
                - cleaned_content: 清理後的回應內容
                - raw_content: 原始模型輸出
                - tokens_generated: 生成的 token 數
                - generation_time: 生成耗時（秒）
            
        Raises:
            APIError: 如果 API 調用失敗
        """
        # 組合完整提示詞
        prompt = self._build_complete_prompt(messages)
        
        # 檢查圖片是否存在
        image_file = Path(image_path)
        if not image_file.exists():
            raise APIError(f"Image file not found: {image_path}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("Calling Qwen3VL API with image", extra={
                    "endpoint": "/generate-with-image",
                    "image": image_file.name,
                    "prompt_length": len(prompt)
                })
                
                # 使用 multipart/form-data 上傳圖片
                with open(image_file, "rb") as f:
                    files = {"image": (image_file.name, f, "image/png")}
                    data = {
                        "prompt": prompt,
                        "temperature": temperature or settings.qwen3vl_temperature,
                        "max_tokens": max_tokens or settings.qwen3vl_max_tokens,
                        "top_p": 0.9
                    }
                    
                    response = await client.post(
                        f"{self.api_url}/generate-with-image",
                        files=files,
                        data=data
                    )
                
                response.raise_for_status()
                result = response.json()
                
                content = result["content"]
                tokens = result.get("tokens_generated", 0)
                gen_time = result.get("generation_time", 0)
                
                # 清理 Qwen3 特殊標籤 (例如 <think>...</think>)
                cleaned_content = clean_qwen3_response(content, debug=True)
                
                logger.info("Qwen3VL image analysis successful", extra={
                    "response_length": len(content),
                    "cleaned_length": len(cleaned_content),
                    "tokens_generated": tokens,
                    "generation_time": f"{gen_time:.2f}s"
                })
                
                return cleaned_content, content, tokens, gen_time
                
        except httpx.HTTPStatusError as e:
            logger.error("Qwen3VL image API HTTP error", extra={
                "status_code": e.response.status_code,
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"Qwen3VL image API error: {e.response.status_code}")
            
        except Exception as e:
            logger.error("Qwen3VL image API error", extra={
                "error": str(e)
            }, exc_info=True)
            raise APIError(f"Qwen3VL image API error: {str(e)}")
    
    def _build_complete_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        組合完整提示詞
        
        將所有訊息（包含 system prompt 和對話歷史）組合成一個完整的提示詞
        這樣每次調用 Qwen3VL API 都是乾淨的，不依賴模型內部的狀態
        
        Args:
            messages: 訊息列表
            
        Returns:
            str: 組合後的完整提示詞
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # System prompt 放在最前面
                prompt_parts.insert(0, f"<|system|>\n{content}\n<|end|>\n")
            elif role == "user":
                prompt_parts.append(f"<|user|>\n{content}\n<|end|>\n")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}\n<|end|>\n")
        
        # 最後加上 assistant 的開頭，讓模型開始生成
        prompt_parts.append("<|assistant|>\n")
        
        complete_prompt = "".join(prompt_parts)
        
        logger.debug("Built complete prompt", extra={
            "message_count": len(messages),
            "prompt_length": len(complete_prompt)
        })
        
        return complete_prompt
    
    async def check_health(self) -> Dict:
        """
        檢查 Qwen3VL 服務健康狀態
        
        Returns:
            dict: 健康狀態資訊
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Qwen3VL health check failed: {e}")
            raise APIError(f"Qwen3VL service not available: {e}")

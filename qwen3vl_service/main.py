"""
Qwen3VL 獨立 API 服務
提供無狀態的 AI 推理接口,支援文字和圖片輸入
"""

import os
import sys
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import uvicorn

# 導入過濾工具
from qwen3_filter import clean_qwen3_response

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """服務配置 - 從主專案的 .env 讀取"""
    
    qwen3vl_model_path: str = "AImodels/Qwen3-VL-4B-Thinking"
    qwen3vl_service_host: str = "0.0.0.0"
    qwen3vl_service_port: int = 8001
    qwen3vl_max_tokens: int = 4096  # 從 .env 讀取，預設 4096
    qwen3vl_temperature: float = 0.85
    
    model_config = SettingsConfigDict(
        env_file="../.env",  # 讀取主專案的 .env
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()


# ==================== API Models ====================

class GenerateRequest(BaseModel):
    """生成請求模型"""
    prompt: str = Field(..., description="完整的提示詞（已組合好的上下文）")
    temperature: Optional[float] = Field(None, description="採樣溫度 (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, description="最大生成 token 數")
    top_p: Optional[float] = Field(0.9, description="核採樣參數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "你是一位青少女角色設計師。請設計一個賽博龐克風格的角色。",
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }


class GenerateResponse(BaseModel):
    """生成回應模型"""
    content: str = Field(..., description="AI 生成的內容")
    model: str = Field(..., description="使用的模型名稱")
    tokens_generated: int = Field(..., description="生成的 token 數量")
    generation_time: float = Field(..., description="生成耗時（秒）")


class HealthResponse(BaseModel):
    """健康檢查回應"""
    status: str
    model_loaded: bool
    model_name: str
    device: str
    
    model_config = {"protected_namespaces": ()}


# ==================== Qwen3VL Model Manager ====================

class Qwen3VLModelManager:
    """Qwen3VL 模型管理器 - 單例模式"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.model = None
        self.processor = None
        self.model_name = "Qwen3-VL-4B-Thinking"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._initialized = True
    
    async def load_model(self):
        """載入模型（啟動時執行一次）"""
        if self.model is not None:
            logger.info("Model already loaded")
            return
        
        async with self._lock:
            if self.model is not None:
                return
            
            logger.info(f"Loading Qwen3VL model from {settings.qwen3vl_model_path}")
            
            try:
                # 在線程池中載入模型（避免阻塞事件循環）
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._executor,
                    self._load_model_sync
                )
                
                logger.info(f"Model loaded successfully on {self.device}")
                
                # 顯示 GPU 記憶體使用
                if torch.cuda.is_available():
                    for i in range(torch.cuda.device_count()):
                        allocated = torch.cuda.memory_allocated(i) / 1024**3
                        reserved = torch.cuda.memory_reserved(i) / 1024**3
                        logger.info(f"GPU {i}: {allocated:.2f}GB allocated / {reserved:.2f}GB reserved")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}", exc_info=True)
                raise RuntimeError(f"Model loading failed: {e}")
    
    def _load_model_sync(self):
        """同步載入模型（在線程池中執行）"""
        if torch.cuda.is_available():
            self.model = AutoModelForImageTextToText.from_pretrained(
                settings.qwen3vl_model_path,
                dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                attn_implementation="sdpa",
            )
        else:
            logger.warning("No GPU detected, using CPU mode (will be slow)")
            self.model = AutoModelForImageTextToText.from_pretrained(
                settings.qwen3vl_model_path,
                device_map="cpu",
                trust_remote_code=True,
            )
        
        self.processor = AutoProcessor.from_pretrained(
            settings.qwen3vl_model_path,
            trust_remote_code=True
        )
    
    async def generate(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,  # 從配置讀取，預設 4096
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        生成回應（無狀態，每次都是乾淨的）
        
        Args:
            prompt: 完整的提示詞
            image_path: 圖片路徑（可選）
            temperature: 採樣溫度
            max_tokens: 最大生成 token 數
            top_p: 核採樣參數
        
        Returns:
            包含生成內容和統計資訊的字典
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # 構建訊息
        if image_path:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": prompt}
                ]
            }]
        else:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }]
        
        # 準備輸入
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(self.model.device)
        
        # 生成
        import time
        start_time = time.time()
        
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                temperature=temperature,
                max_new_tokens=max_tokens,
                do_sample=True,
                top_p=top_p
            )
        
        generation_time = time.time() - start_time
        
        # 解碼
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        tokens_generated = sum(len(ids) for ids in generated_ids_trimmed)
        
        output_text = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        logger.info(f"Generated {tokens_generated} tokens in {generation_time:.2f}s "
                   f"({tokens_generated/generation_time:.2f} tokens/s)")
        
        return {
            "content": output_text,
            "tokens_generated": tokens_generated,
            "generation_time": generation_time
        }


# ==================== FastAPI Application ====================

# 全局模型管理器
model_manager = Qwen3VLModelManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動
    logger.info("Starting Qwen3VL API Service")
    logger.info(f"Configuration: {settings.model_dump()}")
    
    try:
        await model_manager.load_model()
        logger.info("Service ready")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # 關閉
    logger.info("Shutting down Qwen3VL API Service")


app = FastAPI(
    title="Qwen3VL API Service",
    description="無狀態的 Qwen3-VL 推理服務，支援文字和圖片輸入",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查"""
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.model is not None,
        model_name=model_manager.model_name,
        device=model_manager.device
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    純文字生成接口
    
    每次請求都是獨立的，不保留歷史記錄
    調用方需要自行組合完整的提示詞（包含上下文）
    """
    try:
        result = await model_manager.generate(
            prompt=request.prompt,
            temperature=request.temperature or settings.qwen3vl_temperature,
            max_tokens=request.max_tokens or settings.qwen3vl_max_tokens,
            top_p=request.top_p
        )
        
        # 清理 Qwen3 特殊標籤
        cleaned_content = clean_qwen3_response(result["content"], debug=True)
        
        return GenerateResponse(
            content=cleaned_content,
            model=model_manager.model_name,
            tokens_generated=result["tokens_generated"],
            generation_time=result["generation_time"]
        )
        
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate-with-image", response_model=GenerateResponse)
async def generate_with_image(
    prompt: str = Form(..., description="提示詞"),
    image: UploadFile = File(..., description="圖片檔案"),
    temperature: Optional[float] = Form(None),
    max_tokens: Optional[int] = Form(None),
    top_p: Optional[float] = Form(0.9)
):
    """
    圖片 + 文字生成接口
    
    上傳圖片並提供提示詞，AI 會分析圖片並生成回應
    """
    temp_image_path = None
    
    try:
        # 保存臨時圖片 (相對路徑，在專案目錄下)
        temp_dir = Path("../tmp/qwen3vl_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_image_path = temp_dir / f"{image.filename}"
        
        with open(temp_image_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        logger.info(f"Processing image: {image.filename}")
        
        # 生成
        result = await model_manager.generate(
            prompt=prompt,
            image_path=str(temp_image_path),
            temperature=temperature or settings.qwen3vl_temperature,
            max_tokens=max_tokens or settings.qwen3vl_max_tokens,
            top_p=top_p
        )
        
        # 清理 Qwen3 特殊標籤
        cleaned_content = clean_qwen3_response(result["content"], debug=True)
        
        return GenerateResponse(
            content=cleaned_content,
            model=model_manager.model_name,
            tokens_generated=result["tokens_generated"],
            generation_time=result["generation_time"]
        )
        
    except Exception as e:
        logger.error(f"Image generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    finally:
        # 清理臨時檔案
        if temp_image_path and temp_image_path.exists():
            temp_image_path.unlink()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.qwen3vl_service_host,
        port=settings.qwen3vl_service_port,
        reload=False,  # 生產環境不要自動重載
        log_level="info"
    )

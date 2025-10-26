"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Qwen3VL Service API (本地 AI 模型服務)
    qwen3vl_api_url: str = "http://127.0.0.1:8001"
    qwen3vl_model_path: str = "AImodels/Qwen3-VL-4B-Thinking"
    qwen3vl_service_port: int = 8001
    qwen3vl_service_host: str = "0.0.0.0"
    qwen3vl_max_tokens: int = 4096  # 從 .env 讀取，預設 4096
    qwen3vl_temperature: float = 0.85
    
    # ComfyUI API (圖片生成服務)
    comfyui_api_url: str = "http://127.0.0.1:8188"
    comfyui_workflow_path: str = "./workflow/qwen image.json"
    
    # Application Settings (主服務)
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    session_storage_path: str = "./sessions"
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    message_log_file: str = "./logs/message.log"
    
    # Default Image Parameters (預設生圖參數)
    default_image_width: int = 608
    default_image_height: int = 1328
    default_steps: int = 12
    default_cfg: float = 1.0
    default_sampler: str = "dpmpp_2m_sde_gpu"
    default_scheduler: str = "simple"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def sessions_path(self) -> Path:
        """Get sessions directory as Path object."""
        return Path(self.session_storage_path)
    
    @property
    def workflow_path(self) -> Path:
        """Get workflow file as Path object."""
        return Path(self.comfyui_workflow_path)


# Global settings instance
settings = Settings()

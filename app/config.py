"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # GitHub Models API
    github_api_token: str
    github_api_url: str = "https://models.github.ai/inference/chat/completions"
    github_model: str = "gpt-4o"
    
    # ComfyUI API
    comfyui_api_url: str = "http://127.0.0.1:8188"
    comfyui_workflow_path: str = "./workflow/qwen image.json"
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    session_storage_path: str = "./sessions"
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # Default Image Parameters
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

"""Application configuration management."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AI Provider: github | google
    ai_provider: str = "github"

    # GitHub Models API
    github_api_token: str = ""
    github_api_url: str = "https://models.github.ai/inference/chat/completions"
    github_model: str = "gpt-4o"

    # Google AI Studio API
    google_api_key: str = ""
    google_api_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    google_model: str = "gemma-4-27b-it"

    # Prompt Template: qwen | anima
    prompt_template: str = "qwen"

    # ComfyUI API
    comfyui_api_url: str = "http://127.0.0.1:8188"
    # Optional override; auto-derived from prompt_template when not set
    comfyui_workflow_path: Optional[str] = None

    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    session_storage_path: str = "./sessions"
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # Frontend
    frontend_dir: str = "./frontend/dist"

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
        """
        Get workflow file as Path object.

        Auto-derived from prompt_template when COMFYUI_WORKFLOW_PATH is not set:
          qwen  -> ./workflow/qwen image.json
          anima -> ./workflow/Anima.json
        """
        if self.comfyui_workflow_path:
            return Path(self.comfyui_workflow_path)
        if self.prompt_template.lower() == "anima":
            return Path("./workflow/Anima.json")
        return Path("./workflow/qwen image.json")


# Global settings instance
settings = Settings()

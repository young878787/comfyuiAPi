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
    google_model: str = "gemma-4-31b-it"

    # Prompt Template: qwen | anima
    prompt_template: str = "qwen"

    # ComfyUI API
    comfyui_api_url: str = "http://127.0.0.1:8188"

    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    # Preferred backend binding port for server startup. Falls back to APP_PORT.
    backend_port: Optional[int] = None
    outputs_dir: str = "./outputs"
    default_workflow: str = "anima"
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
    def outputs_path(self) -> Path:
        """Get outputs directory as Path object."""
        return Path(self.outputs_dir)

    @property
    def server_port(self) -> int:
        """Get backend startup port, preferring BACKEND_PORT when set."""
        return self.backend_port if self.backend_port is not None else self.app_port

    @property
    def workflow_path(self) -> Path:
        """
        Get default workflow file as Path object (for ComfyUIAdapter initialization compatibility).
        """
        if self.default_workflow.lower() == "anima":
            return Path("./workflow/Anima.json")
        return Path("./workflow/qwen image.json")


# Global settings instance
settings = Settings()

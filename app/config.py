"""Application configuration management."""

from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AI Provider: opencode | google
    ai_provider: str = "opencode"

    # OpenCode API
    opencode_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("opencode_api_key", "OPENCODE_API_KEY", "OPENCODE_GO_API_KEY")
    )
    opencode_api_url: str = Field(
        default="https://opencode.ai/zen/go/v1/chat/completions",
        validation_alias=AliasChoices(
            "opencode_api_url", 
            "OPENCODE_API_URL", 
            "OPENCODE_CHAT_COMPLETIONS_URL",
            "OPENCODE_GO_API_URL",
            "OPENCODE_GO_CHAT_COMPLETIONS_URL"
        )
    )
    opencode_model: str = Field(
        default="deepseek-v4-flash",
        validation_alias=AliasChoices(
            "opencode_model",
            "OPENCODE_MODEL",
            "OPENCODE_TRANSLATION_MODEL",
            "OPENCODE_GO_MODEL",
            "OPENCODE_GO_PUNCTUATION_MODEL"
        )
    )
    opencode_thinking: str = Field(
        default="disabled",
        validation_alias=AliasChoices(
            "opencode_thinking",
            "OPENCODE_THINKING",
            "OPENCODE_GO_THINKING"
        )
    )

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

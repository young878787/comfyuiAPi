"""Data Transfer Objects for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class GenerateRequest(BaseModel):
    """Request options for Prompt editor AI and ComfyUI generation."""
    prompt: Optional[str] = Field(default=None, description="Original positive prompt")
    idea: Optional[str] = Field(default=None, description="Modification idea or prompt expansion")
    attempts: Optional[int] = Field(default=1, ge=1, le=5, description="Number of image generation attempts")
    workflow: str = Field(default="anima", description="Target workflow file identifier")
    width: Optional[int] = Field(default=None, ge=256, le=2048)
    height: Optional[int] = Field(default=None, ge=256, le=2048)
    steps: Optional[int] = Field(default=None, ge=1, le=100)
    cfg: Optional[float] = Field(default=None, ge=0.1, le=30.0)
    seed: Optional[int] = Field(default=None, ge=0, le=2**32-1)
    sampler: Optional[str] = Field(default=None)
    scheduler: Optional[str] = Field(default=None)
    negative_prompt: Optional[str] = Field(default=None)
    image_base64: Optional[str] = Field(default=None, description="Reference image base64")
    image_mime_type: Optional[str] = Field(default="image/jpeg", description="Reference image mime type")
    checkpoint: Optional[str] = Field(default=None, description="Dynamic checkpoint model name to swap in loader")



class WorkflowInfo(BaseModel):
    """Workflow structure representation."""
    name: str
    display_name: str
    file: str
    defaults: Dict[str, Any]


class StatusResponse(BaseModel):
    """ComfyUI server and application status response."""
    connected: bool
    comfyui_url: str
    workflows: List[WorkflowInfo]
    default_workflow: str
    ai_provider: str


class ImageResponse(BaseModel):
    """Individual image details response."""
    filename: str
    url: str
    metadata: Dict[str, Any]


class ImageListResponse(BaseModel):
    """Image list response grouped by date."""
    date: str
    images: List[str]
    latest_image: Optional[str] = None


class OpenFolderRequest(BaseModel):
    """Request options for opening local file manager at the output path."""
    date_str: str
    filename: Optional[str] = None
    workflow: Optional[str] = "anima"


"""Data Transfer Objects for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.config import settings  # 導入配置


# Session DTOs
class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    title: Optional[str] = None


class SessionUpdateRequest(BaseModel):
    """Request to update session."""
    title: str = Field(..., min_length=1, max_length=100)


class SessionResponse(BaseModel):
    """Session response."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    image_count: int


# Chat DTOs
class ChatSendRequest(BaseModel):
    """Request to send a chat message."""
    session_id: str
    message: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Message response."""
    id: str
    role: str
    content: str
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    session_id: str
    messages: List[MessageResponse]


# Image DTOs
class ImageGenerateRequest(BaseModel):
    """Request to generate an image."""
    session_id: str
    positive_prompt: str = Field(..., min_length=1, max_length=5000)
    negative_prompt: str = Field(default="", max_length=5000)
    width: int = Field(default_factory=lambda: settings.default_image_width, ge=256, le=2048)
    height: int = Field(default_factory=lambda: settings.default_image_height, ge=256, le=2048)
    steps: int = Field(default_factory=lambda: settings.default_steps, ge=1, le=100)
    cfg: float = Field(default_factory=lambda: settings.default_cfg, ge=0.1, le=30.0)
    seed: Optional[int] = Field(default=None, ge=0, le=2**32-1)
    sampler: str = Field(default_factory=lambda: settings.default_sampler)
    scheduler: str = Field(default_factory=lambda: settings.default_scheduler)


class ImageResponse(BaseModel):
    """Image generation response."""
    filename: str
    url: str
    metadata: dict


class ImageListResponse(BaseModel):
    """Image list response."""
    session_id: str
    images: List[str]
    latest_image: Optional[str] = None

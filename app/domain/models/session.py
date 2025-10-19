"""Session domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """
    Session entity representing a conversation session.
    
    Attributes:
        id: Unique session identifier (e.g., session_20251016_001)
        title: Session title (editable by user)
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        message_count: Number of messages in this session
        image_count: Number of images generated in this session
    """
    
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    image_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "image_count": self.image_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create session from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=data.get("message_count", 0),
            image_count=data.get("image_count", 0),
        )

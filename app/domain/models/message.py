"""Message domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Message:
    """
    Message entity representing a chat message.
    
    Attributes:
        id: Unique message identifier
        role: Message role ("user" or "assistant")
        content: Message content
        timestamp: Message creation timestamp
        metadata: Additional metadata (e.g., contains_prompt flag)
    """
    
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create message from dictionary."""
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )

"""Session repository for data persistence."""

import json
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.domain.models import Session, Message
from app.domain.exceptions import SessionNotFoundError, SessionCreateError

logger = logging.getLogger(__name__)


class SessionRepository:
    """Repository for managing session data persistence."""
    
    def __init__(self):
        """Initialize repository with storage path."""
        self.storage_path = settings.sessions_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get session directory path."""
        return self.storage_path / session_id
    
    def _get_config_path(self, session_id: str) -> Path:
        """Get session config file path."""
        return self._get_session_path(session_id) / "config.json"
    
    def _get_messages_path(self, session_id: str) -> Path:
        """Get session messages file path."""
        return self._get_session_path(session_id) / "chat_history.json"
    
    def _get_images_path(self, session_id: str) -> Path:
        """Get session images directory path."""
        return self._get_session_path(session_id) / "images"
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Find next available number
        existing_sessions = [
            d.name for d in self.storage_path.iterdir()
            if d.is_dir() and d.name.startswith(f"session_{date_str}")
        ]
        
        if not existing_sessions:
            counter = 1
        else:
            counters = []
            for session_name in existing_sessions:
                try:
                    counter = int(session_name.split('_')[-1])
                    counters.append(counter)
                except ValueError:
                    continue
            counter = max(counters) + 1 if counters else 1
        
        return f"session_{date_str}_{counter:03d}"
    
    def _generate_default_title(self, session_count: int) -> str:
        """Generate default session title."""
        return f"新對話 {session_count + 1}"
    
    async def create(self, title: Optional[str] = None) -> Session:
        """
        Create a new session.
        
        Args:
            title: Session title (optional, will generate if not provided)
            
        Returns:
            Session: Created session
            
        Raises:
            SessionCreateError: If session creation fails
        """
        try:
            session_id = self._generate_session_id()
            session_path = self._get_session_path(session_id)
            
            # Create session directory structure
            session_path.mkdir(parents=True, exist_ok=True)
            images_path = self._get_images_path(session_id)
            images_path.mkdir(parents=True, exist_ok=True)
            
            # Generate title if not provided
            if title is None:
                existing_count = len(self.list_all())
                title = self._generate_default_title(existing_count)
            
            # Create session object
            now = datetime.now()
            session = Session(
                id=session_id,
                title=title,
                created_at=now,
                updated_at=now,
                message_count=0,
                image_count=0
            )
            
            # Save config
            config_path = self._get_config_path(session_id)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Create empty messages file
            messages_path = self._get_messages_path(session_id)
            with open(messages_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            
            logger.info("Session created", extra={
                "session_id": session_id,
                "title": title
            })
            
            return session
            
        except Exception as e:
            logger.error("Failed to create session", extra={
                "error": str(e)
            }, exc_info=True)
            raise SessionCreateError(f"Failed to create session: {str(e)}")
    
    async def get(self, session_id: str) -> Session:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session: Session object
            
        Raises:
            SessionNotFoundError: If session not found
        """
        config_path = self._get_config_path(session_id)
        
        if not config_path.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Session.from_dict(data)
            
        except Exception as e:
            logger.error("Failed to load session", extra={
                "session_id": session_id,
                "error": str(e)
            }, exc_info=True)
            raise SessionNotFoundError(f"Failed to load session: {str(e)}")
    
    async def update(self, session: Session) -> None:
        """
        Update session data.
        
        Args:
            session: Session object to update
            
        Raises:
            SessionNotFoundError: If session not found
        """
        config_path = self._get_config_path(session.id)
        
        if not config_path.exists():
            raise SessionNotFoundError(f"Session not found: {session.id}")
        
        try:
            session.updated_at = datetime.now()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info("Session updated", extra={
                "session_id": session.id
            })
            
        except Exception as e:
            logger.error("Failed to update session", extra={
                "session_id": session.id,
                "error": str(e)
            }, exc_info=True)
            raise
    
    async def delete(self, session_id: str) -> None:
        """
        Delete session and all its data.
        
        Args:
            session_id: Session ID
            
        Raises:
            SessionNotFoundError: If session not found
        """
        session_path = self._get_session_path(session_id)
        
        if not session_path.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        try:
            shutil.rmtree(session_path)
            
            logger.info("Session deleted", extra={
                "session_id": session_id
            })
            
        except Exception as e:
            logger.error("Failed to delete session", extra={
                "session_id": session_id,
                "error": str(e)
            }, exc_info=True)
            raise
    
    def list_all(self) -> List[Session]:
        """
        List all sessions.
        
        Returns:
            List[Session]: List of all sessions, sorted by updated_at desc
        """
        sessions = []
        
        for session_dir in self.storage_path.iterdir():
            if not session_dir.is_dir():
                continue
            
            try:
                config_path = session_dir / "config.json"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append(Session.from_dict(data))
            except Exception as e:
                logger.warning("Failed to load session", extra={
                    "session_dir": str(session_dir),
                    "error": str(e)
                })
                continue
        
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        return sessions
    
    async def get_messages(self, session_id: str) -> List[Message]:
        """
        Get all messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[Message]: List of messages
            
        Raises:
            SessionNotFoundError: If session not found
        """
        messages_path = self._get_messages_path(session_id)
        
        if not messages_path.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return [Message.from_dict(msg) for msg in data]
            
        except Exception as e:
            logger.error("Failed to load messages", extra={
                "session_id": session_id,
                "error": str(e)
            }, exc_info=True)
            raise
    
    async def save_messages(self, session_id: str, messages: List[Message]) -> None:
        """
        Save messages for a session.
        
        Args:
            session_id: Session ID
            messages: List of messages to save
            
        Raises:
            SessionNotFoundError: If session not found
        """
        messages_path = self._get_messages_path(session_id)
        
        if not messages_path.parent.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        try:
            messages_data = [msg.to_dict() for msg in messages]
            
            with open(messages_path, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Messages saved", extra={
                "session_id": session_id,
                "message_count": len(messages)
            })
            
        except Exception as e:
            logger.error("Failed to save messages", extra={
                "session_id": session_id,
                "error": str(e)
            }, exc_info=True)
            raise

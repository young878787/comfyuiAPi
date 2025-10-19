"""Session service for session management."""

import logging
from typing import List, Optional

from app.domain.models import Session
from app.infrastructure.repositories.session_repository import SessionRepository
from app.domain.exceptions import SessionNotFoundError

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing sessions."""
    
    def __init__(self, session_repository: SessionRepository):
        """
        Initialize service with dependencies.
        
        Args:
            session_repository: Session repository
        """
        self.session_repository = session_repository
    
    async def create_session(self, title: Optional[str] = None) -> Session:
        """
        Create a new session.
        
        Args:
            title: Session title (optional)
            
        Returns:
            Session: Created session
        """
        session = await self.session_repository.create(title)
        
        logger.info("Session created via service", extra={
            "session_id": session.id,
            "title": session.title
        })
        
        return session
    
    async def get_session(self, session_id: str) -> Session:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session: Session object
            
        Raises:
            SessionNotFoundError: If session not found
        """
        return await self.session_repository.get(session_id)
    
    async def update_session_title(self, session_id: str, title: str) -> Session:
        """
        Update session title.
        
        Args:
            session_id: Session ID
            title: New title
            
        Returns:
            Session: Updated session
            
        Raises:
            SessionNotFoundError: If session not found
        """
        session = await self.session_repository.get(session_id)
        session.title = title
        await self.session_repository.update(session)
        
        logger.info("Session title updated", extra={
            "session_id": session_id,
            "new_title": title
        })
        
        return session
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete session.
        
        Args:
            session_id: Session ID
            
        Raises:
            SessionNotFoundError: If session not found
        """
        await self.session_repository.delete(session_id)
        
        logger.info("Session deleted via service", extra={
            "session_id": session_id
        })
    
    async def list_sessions(self) -> List[Session]:
        """
        List all sessions.
        
        Returns:
            List[Session]: List of sessions
        """
        return self.session_repository.list_all()
    
    async def increment_message_count(self, session_id: str) -> None:
        """
        Increment message count for session.
        
        Args:
            session_id: Session ID
        """
        session = await self.session_repository.get(session_id)
        session.message_count += 1
        await self.session_repository.update(session)
    
    async def increment_image_count(self, session_id: str) -> None:
        """
        Increment image count for session.
        
        Args:
            session_id: Session ID
        """
        session = await self.session_repository.get(session_id)
        session.image_count += 1
        await self.session_repository.update(session)

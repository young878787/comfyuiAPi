"""Chat service for AI conversation management."""

import logging
import uuid
from typing import List
from datetime import datetime

from app.domain.models import Message
from app.domain.models.prompt_template import CHARACTER_DESIGNER_TEMPLATE
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.adapters.github_model_adapter import GitHubModelAdapter
from app.application.services.session_service import SessionService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations."""
    
    def __init__(
        self,
        session_repository: SessionRepository,
        github_adapter: GitHubModelAdapter,
        session_service: SessionService
    ):
        """
        Initialize service with dependencies.
        
        Args:
            session_repository: Session repository
            github_adapter: GitHub Models API adapter
            session_service: Session service
        """
        self.session_repository = session_repository
        self.github_adapter = github_adapter
        self.session_service = session_service
        self.prompt_template = CHARACTER_DESIGNER_TEMPLATE
    
    async def send_message(self, session_id: str, user_message: str) -> Message:
        """
        Send a message and get AI response.
        
        Args:
            session_id: Session ID
            user_message: User's message
            
        Returns:
            Message: AI assistant's response message
        """
        # Load existing messages
        messages = await self.session_repository.get_messages(session_id)
        
        # Create user message
        user_msg = Message(
            id=str(uuid.uuid4()),
            role="user",
            content=user_message,
            timestamp=datetime.now()
        )
        
        messages.append(user_msg)
        
        # Build context for AI
        api_messages = self._build_api_messages(messages)
        
        # Get AI response
        logger.info("Requesting AI response", extra={
            "session_id": session_id,
            "message_count": len(api_messages)
        })
        
        ai_content = await self.github_adapter.generate_response(
            api_messages,
            temperature=self.prompt_template.temperature,
            max_tokens=self.prompt_template.max_tokens
        )
        
        # Create assistant message
        assistant_msg = Message(
            id=str(uuid.uuid4()),
            role="assistant",
            content=ai_content,
            timestamp=datetime.now(),
            metadata={"model": self.prompt_template.model}
        )
        
        messages.append(assistant_msg)
        
        # Save messages
        await self.session_repository.save_messages(session_id, messages)
        
        # Update message count
        await self.session_service.increment_message_count(session_id)
        
        logger.info("AI response generated", extra={
            "session_id": session_id,
            "response_length": len(ai_content)
        })
        
        return assistant_msg
    
    async def get_chat_history(self, session_id: str) -> List[Message]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[Message]: List of messages
        """
        return await self.session_repository.get_messages(session_id)
    
    def _build_api_messages(self, messages: List[Message]) -> List[dict]:
        """
        Build API messages with system prompt.
        
        Args:
            messages: List of messages
            
        Returns:
            List[dict]: API-formatted messages
        """
        api_messages = [
            {
                "role": "system",
                "content": self.prompt_template.system_prompt
            }
        ]
        
        # Add conversation history
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return api_messages

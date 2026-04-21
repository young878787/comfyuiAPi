"""Chat service for AI conversation management."""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.domain.models import Message
from app.domain.models.prompt_template import get_template
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.adapters.base_ai_adapter import BaseAIAdapter
from app.application.services.session_service import SessionService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations."""

    def __init__(
        self,
        session_repository: SessionRepository,
        ai_adapter: BaseAIAdapter,
        session_service: SessionService,
    ):
        """
        Initialize service with dependencies.

        Args:
            session_repository: Session repository
            ai_adapter: Any AI provider adapter (GitHub or Google)
            session_service: Session service
        """
        self.session_repository = session_repository
        self.ai_adapter = ai_adapter
        self.session_service = session_service
        self.prompt_template = get_template(settings.prompt_template)

        logger.info(
            "ChatService initialised",
            extra={
                "template": self.prompt_template.name,
                "provider": settings.ai_provider,
            },
        )

    async def send_message(self, session_id: str, user_message: str, image_base64: Optional[str] = None, image_mime_type: Optional[str] = None) -> Message:
        """
        Send a message and get AI response.

        Args:
            session_id: Session ID
            user_message: User's message

        Returns:
            Message: AI assistant's response message
        """
        messages = await self.session_repository.get_messages(session_id)

        user_msg = Message(
            id=str(uuid.uuid4()),
            role="user",
            content=user_message,
            timestamp=datetime.now(),
        )
        messages.append(user_msg)

        api_messages = self._build_api_messages(messages, image_base64, image_mime_type)

        logger.info(
            "Requesting AI response",
            extra={"session_id": session_id, "message_count": len(api_messages)},
        )

        ai_content = await self.ai_adapter.generate_response(
            api_messages,
            temperature=self.prompt_template.temperature,
            max_tokens=self.prompt_template.max_tokens,
        )

        assistant_msg = Message(
            id=str(uuid.uuid4()),
            role="assistant",
            content=ai_content,
            timestamp=datetime.now(),
            metadata={
                "model": self.prompt_template.model,
                "provider": settings.ai_provider,
                "template": settings.prompt_template,
            },
        )
        messages.append(assistant_msg)

        await self.session_repository.save_messages(session_id, messages)
        await self.session_service.increment_message_count(session_id)

        logger.info(
            "AI response generated",
            extra={"session_id": session_id, "response_length": len(ai_content)},
        )

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

    def _build_api_messages(self, messages: List[Message], image_base64: Optional[str] = None, image_mime_type: Optional[str] = None) -> List[dict]:
        """
        Prepend the active system prompt and format messages for the API.

        Args:
            messages: Conversation messages
            image_base64: Optional base64-encoded image
            image_mime_type: Optional MIME type for the image

        Returns:
            List[dict]: API-formatted message list
        """
        api_messages = [
            {
                "role": "system",
                "content": self.prompt_template.system_prompt,
            }
        ]
        for i, msg in enumerate(messages):
            # For the last user message, include image if provided
            if image_base64 and i == len(messages) - 1 and msg.role == "user":
                api_messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": msg.content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime_type or 'image/jpeg'};base64,{image_base64}"
                            }
                        }
                    ]
                })
            else:
                api_messages.append({"role": msg.role, "content": msg.content})
        return api_messages

"""Chat service for AI conversation management."""

import logging
import uuid
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile

from app.domain.models import Message
from app.domain.models.prompt_template import CHARACTER_DESIGNER_TEMPLATE
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.adapters.qwen3vl_adapter import Qwen3VLAdapter
from app.application.services.session_service import SessionService
from app.infrastructure.logging import get_message_logger

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations."""
    
    def __init__(
        self,
        session_repository: SessionRepository,
        qwen3vl_adapter: Qwen3VLAdapter,
        session_service: SessionService
    ):
        """
        Initialize service with dependencies.
        
        Args:
            session_repository: Session repository
            qwen3vl_adapter: Qwen3VL API adapter
            session_service: Session service
        """
        self.session_repository = session_repository
        self.qwen3vl_adapter = qwen3vl_adapter
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
        
        # 記錄用戶訊息到 message.log
        msg_logger = get_message_logger()
        msg_logger.log_user_message(
            session_id=session_id,
            content=user_message
        )
        
        # Build context for AI
        api_messages = self._build_api_messages(messages)
        
        # Get AI response
        logger.info("Requesting AI response from Qwen3VL", extra={
            "session_id": session_id,
            "message_count": len(api_messages)
        })
        
        ai_content, raw_content, tokens, gen_time = await self.qwen3vl_adapter.generate_response(
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
            metadata={"model": "Qwen3-VL-4B-Thinking"}
        )
        
        messages.append(assistant_msg)
        
        # 記錄 AI 回應到 message.log
        msg_logger = get_message_logger()
        msg_logger.log_ai_response(
            session_id=session_id,
            content=ai_content,
            model="Qwen3-VL-4B-Thinking",
            tokens=tokens,
            generation_time=gen_time,
            raw_content=raw_content
        )
        
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


    async def send_message_with_image(
        self,
        session_id: str,
        user_message: str,
        image_file: UploadFile
    ) -> Message:
        """
        Send a message with image and get AI response.
        
        Args:
            session_id: Session ID
            user_message: User's message
            image_file: Uploaded image file
            
        Returns:
            Message: AI assistant's response message
        """
        # Save image to temporary directory (relative to project root)
        temp_dir = Path("./tmp/qwen3vl_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"{session_id}_{timestamp}_{image_file.filename}"
        image_path = temp_dir / image_filename
        
        # Save uploaded file
        try:
            content = await image_file.read()
            with open(image_path, "wb") as f:
                f.write(content)
            
            logger.info("Image saved for analysis", extra={
                "session_id": session_id,
                "image_name": image_filename,
                "file_size": len(content)
            })
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise
        
        # Load existing messages
        messages = await self.session_repository.get_messages(session_id)
        
        # Create user message (include image info in metadata)
        user_msg = Message(
            id=str(uuid.uuid4()),
            role="user",
            content=user_message,
            timestamp=datetime.now(),
            metadata={
                "has_image": True,
                "image_filename": image_filename
            }
        )
        
        messages.append(user_msg)
        
        # Log user message
        msg_logger = get_message_logger()
        msg_logger.log_user_message(
            session_id=session_id,
            content=f"[Image: {image_filename}] {user_message}"
        )
        
        # Build context for AI
        api_messages = self._build_api_messages(messages)
        
        # Get AI response with image
        logger.info("Requesting AI response with image", extra={
            "session_id": session_id,
            "image_name": image_filename
        })
        
        try:
            ai_content, raw_content, tokens, gen_time = await self.qwen3vl_adapter.generate_with_image(
                messages=api_messages,
                image_path=str(image_path),
                temperature=self.prompt_template.temperature,
                max_tokens=self.prompt_template.max_tokens
            )
        finally:
            # Clean up temporary image file
            if image_path.exists():
                image_path.unlink()
                logger.info(f"Cleaned up temporary image: {image_filename}")
        
        # Create assistant message
        assistant_msg = Message(
            id=str(uuid.uuid4()),
            role="assistant",
            content=ai_content,
            timestamp=datetime.now(),
            metadata={"model": "Qwen3-VL-4B-Thinking"}
        )
        
        messages.append(assistant_msg)
        
        # Log AI response
        msg_logger.log_ai_response(
            session_id=session_id,
            content=ai_content,
            model="Qwen3-VL-4B-Thinking",
            tokens=tokens,
            generation_time=gen_time,
            raw_content=raw_content
        )
        
        # Save messages
        await self.session_repository.save_messages(session_id, messages)
        
        # Update message count
        await self.session_service.increment_message_count(session_id)
        
        logger.info("AI response with image generated", extra={
            "session_id": session_id,
            "response_length": len(ai_content)
        })
        
        return assistant_msg

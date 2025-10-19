"""Chat conversation routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.application.dtos.common import (
    ChatSendRequest,
    MessageResponse,
    ChatHistoryResponse
)
from app.application.services.chat_service import ChatService
from app.application.services.session_service import SessionService
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.adapters.github_model_adapter import GitHubModelAdapter
from app.domain.exceptions import SessionNotFoundError, APIError

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Dependency to get chat service."""
    session_repository = SessionRepository()
    github_adapter = GitHubModelAdapter()
    session_service = SessionService(session_repository)
    return ChatService(session_repository, github_adapter, session_service)


@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: ChatSendRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Send a chat message and get AI response."""
    try:
        message = await service.send_message(request.session_id, request.message)
        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp
        )
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a session."""
    try:
        messages = await service.get_chat_history(session_id)
        return ChatHistoryResponse(
            session_id=session_id,
            messages=[
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp
                )
                for msg in messages
            ]
        )
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

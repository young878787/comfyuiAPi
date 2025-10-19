"""Session management routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.application.dtos.common import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse
)
from app.application.services.session_service import SessionService
from app.infrastructure.repositories.session_repository import SessionRepository
from app.domain.exceptions import SessionNotFoundError, SessionCreateError

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def get_session_service() -> SessionService:
    """Dependency to get session service."""
    repository = SessionRepository()
    return SessionService(repository)


@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    service: SessionService = Depends(get_session_service)
):
    """Create a new session."""
    try:
        session = await service.create_session(request.title)
        return SessionResponse(**session.to_dict())
    except SessionCreateError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    service: SessionService = Depends(get_session_service)
):
    """List all sessions."""
    sessions = await service.list_sessions()
    return [SessionResponse(**s.to_dict()) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """Get session by ID."""
    try:
        session = await service.get_session(session_id)
        return SessionResponse(**session.to_dict())
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{session_id}/title", response_model=SessionResponse)
async def update_session_title(
    session_id: str,
    request: SessionUpdateRequest,
    service: SessionService = Depends(get_session_service)
):
    """Update session title."""
    try:
        session = await service.update_session_title(session_id, request.title)
        return SessionResponse(**session.to_dict())
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """Delete session."""
    try:
        await service.delete_session(session_id)
        return {"success": True}
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

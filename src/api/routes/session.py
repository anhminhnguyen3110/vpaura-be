from fastapi import APIRouter, Depends, status
from ...services.session import SessionService
from ...schemas.session import SessionCreate, SessionResponse, SessionUpdate
from ...database.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new session."""
    service = SessionService(session)
    return await service.create_session(request)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get a session by ID."""
    service = SessionService(session)
    return await service.get_by_id(session_id)


@router.get("/user/{user_id}", response_model=List[SessionResponse])
async def get_user_sessions(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    """Get all sessions for a user."""
    service = SessionService(session)
    return await service.get_by_user(user_id, skip, limit)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    request: SessionUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """Update a session."""
    service = SessionService(session)
    return await service.update_session(session_id, request)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Delete a session."""
    service = SessionService(session)
    await service.delete_session(session_id)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...schemas.user import UserCreate, UserResponse
from ...services.user import UserService
from ...database.session import get_db_session

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse)
async def create_user(
    request: UserCreate,
    session: AsyncSession = Depends(get_db_session)
):
    service = UserService(session)
    return await service.create_user(request)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = UserService(session)
    return await service.get_by_id(user_id)


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    service = UserService(session)
    return await service.get_all(skip, limit)

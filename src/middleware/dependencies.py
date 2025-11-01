from fastapi import Depends, Header, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.session import get_async_session
from ..constants.errors import ErrorMessages


async def get_db_session():
    async for session in get_async_session():
        yield session


async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail=ErrorMessages.INVALID_REQUEST
        )
    return x_api_key


async def get_current_user(
    api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    pass

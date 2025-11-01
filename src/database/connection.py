from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text
from .engine import engine


@asynccontextmanager
async def get_connection():
    async with engine.begin() as conn:
        yield conn


async def check_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

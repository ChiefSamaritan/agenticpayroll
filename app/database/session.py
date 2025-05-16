from app.database.connection import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

from typing import AsyncGenerator

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
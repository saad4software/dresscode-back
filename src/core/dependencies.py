from typing import Annotated

from fastapi import Depends
from src.core.config import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


engine = create_async_engine(config.db_url, connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession,
)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

SessionDep = Annotated[AsyncSession, Depends(get_session)]
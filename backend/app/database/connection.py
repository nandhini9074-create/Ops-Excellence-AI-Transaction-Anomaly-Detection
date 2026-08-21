from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Replace protocol to ensure asyncpg is used by SQLAlchemy
dsn = settings.DATABASE_URL
if dsn.startswith("postgresql://"):
    dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    dsn,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db_pool():
    logger.info("SQLAlchemy async engine initialized.")

async def close_db_pool():
    logger.info("Closing SQLAlchemy async engine...")
    await engine.dispose()
    logger.info("Database engine closed.")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a SQLAlchemy AsyncSession.
    """
    async with async_session_maker() as session:
        yield session

# Provide dummy _pool to not break imports completely before full refactor
class DummyPool:
    def acquire(self):
        raise NotImplementedError("Raw asyncpg pool is deprecated. Use async_session_maker().")
_pool = DummyPool()

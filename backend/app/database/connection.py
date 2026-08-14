import asyncpg
from typing import AsyncGenerator
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Global pool instance
_pool: asyncpg.Pool = None

async def init_db_pool():
    global _pool
    logger.info("Initializing asyncpg database pool...")
    
    # We replace postgresql+asyncpg:// with postgres:// or postgresql://
    # asyncpg understands postgresql:// 
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logger.info("Database pool created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise

async def close_db_pool():
    global _pool
    if _pool:
        logger.info("Closing asyncpg database pool...")
        await _pool.close()
        logger.info("Database pool closed.")

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency to get a connection from the pool.
    """
    if not _pool:
        raise RuntimeError("Database pool has not been initialized.")
        
    async with _pool.acquire() as connection:
        yield connection

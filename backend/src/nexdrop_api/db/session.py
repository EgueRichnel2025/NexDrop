"""Asynchronous database session dependencies and readiness probe."""

import logging
from collections.abc import AsyncIterator

from fastapi import HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session when PostgreSQL is configured."""
    session_factory: async_sessionmaker[AsyncSession] | None = request.app.state.session_factory
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured.",
        )

    async with session_factory() as session:
        yield session


async def database_is_ready(request: Request) -> bool:
    """Check PostgreSQL with a lightweight query; never expose driver errors."""
    session_factory: async_sessionmaker[AsyncSession] | None = request.app.state.session_factory
    if session_factory is None:
        return False

    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Database readiness check failed.")
        return False

    return True

"""FastAPI application factory and ASGI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nexdrop_api.api.router import api_router
from nexdrop_api.core.config import Settings, get_settings
from nexdrop_api.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an application instance without opening a database connection."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    engine: AsyncEngine | None = None
    session_factory: async_sessionmaker[AsyncSession] | None = None
    if app_settings.database_url is not None:
        engine = create_async_engine(
            app_settings.database_url,
            pool_pre_ping=True,
            pool_timeout=5,
            connect_args={"connect_timeout": 5},
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is not None:
            await engine.dispose()

    application = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.state.engine = engine
    application.state.session_factory = session_factory
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(api_router, prefix=app_settings.api_v1_prefix)
    return application


app = create_app()

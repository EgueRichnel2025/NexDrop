"""Shared API and PostgreSQL integration-test fixtures."""

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from nexdrop_api.core.config import Settings
from nexdrop_api.main import create_app


@pytest.fixture
def test_settings(monkeypatch) -> Settings:
    """Provide deterministic settings without reading a developer's environment."""
    for name in (
        "NEXDROP_APP_NAME",
        "NEXDROP_ENVIRONMENT",
        "NEXDROP_API_V1_PREFIX",
        "NEXDROP_SERVER_HOST",
        "NEXDROP_SERVER_PORT",
        "NEXDROP_SERVER_RELOAD",
        "NEXDROP_LOG_LEVEL",
        "NEXDROP_CORS_ORIGINS",
        "NEXDROP_DATABASE_URL",
        "NEXDROP_POSTGRES_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)
    return Settings(_env_file=None, environment="testing", database_url=None, cors_origins=[])


@pytest.fixture
def app(test_settings: Settings):
    """Create an isolated FastAPI application for each test."""
    return create_app(test_settings)


@pytest_asyncio.fixture
async def migrated_test_db():
    """Open a rollback-only transaction against the dedicated migrated test database."""
    database_url = os.getenv("NEXDROP_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set NEXDROP_TEST_DATABASE_URL to run PostgreSQL integration tests.")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                yield connection
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def migrated_test_engine():
    """Provide an engine for explicit multi-connection PostgreSQL concurrency tests."""
    database_url = os.getenv("NEXDROP_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set NEXDROP_TEST_DATABASE_URL to run PostgreSQL integration tests.")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()

"""Shared API test fixtures."""

import pytest

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

"""Health endpoint behavior tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from nexdrop_api.core.config import Settings
from nexdrop_api.db.session import database_is_ready
from nexdrop_api.main import create_app


@pytest.mark.asyncio
async def test_liveness_does_not_require_database(app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_returns_503_when_database_is_not_configured(app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "unavailable"},
    }


@pytest.mark.asyncio
async def test_readiness_returns_200_when_database_check_succeeds(app) -> None:
    async def database_available() -> bool:
        return True

    app.dependency_overrides[database_is_ready] = database_available
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "available"},
    }


@pytest.mark.asyncio
async def test_readiness_returns_503_when_database_check_fails(app) -> None:
    async def database_unavailable() -> bool:
        return False

    app.dependency_overrides[database_is_ready] = database_unavailable
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "unavailable"


def test_application_engine_creation_does_not_connect_to_postgres() -> None:
    settings = Settings(
        _env_file=None,
        environment="testing",
        database_url="postgresql+psycopg://nexdrop:unused@127.0.0.1:5432/nexdrop",
    )
    app = create_app(settings)

    assert app.state.engine is not None
    assert app.state.session_factory is not None

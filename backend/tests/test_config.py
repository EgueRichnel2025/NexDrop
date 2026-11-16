"""Application settings validation tests."""

import pytest
from pydantic import ValidationError

from nexdrop_api.core.config import Settings


def test_settings_use_expected_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.app_name == "NexDrop API"
    assert settings.environment == "development"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.server_host == "127.0.0.1"
    assert settings.server_port == 8765
    assert settings.server_reload is True
    assert settings.database_url is None
    assert settings.cors_origins == []


def test_settings_read_prefixed_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("NEXDROP_ENVIRONMENT", "staging")
    monkeypatch.setenv("NEXDROP_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("NEXDROP_SERVER_PORT", "8766")
    monkeypatch.setenv("NEXDROP_SERVER_RELOAD", "false")
    monkeypatch.setenv("NEXDROP_CORS_ORIGINS", '["https://desktop.example.com"]')
    settings = Settings(_env_file=None)
    assert settings.environment == "staging"
    assert settings.log_level == "WARNING"
    assert settings.server_port == 8766
    assert settings.server_reload is False
    assert settings.cors_origins == ["https://desktop.example.com"]


def test_server_port_must_be_valid() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, server_port=70000)


def test_database_url_requires_async_psycopg_dialect() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://user:pass@localhost/db")

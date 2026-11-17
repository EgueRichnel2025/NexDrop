"""Alembic environment configured for asynchronous SQLAlchemy and Psycopg."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import nexdrop_api.db.models  # noqa: F401 — register every mapped table for Alembic.
from nexdrop_api.core.config import get_settings
from nexdrop_api.core.event_loop import configure_event_loop_policy
from nexdrop_api.db.base import Base

configure_event_loop_policy()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def configured_database_url() -> str:
    """Load the database URL without printing credentials."""
    database_url = get_settings().database_url
    if database_url is None:
        raise RuntimeError(
            "NEXDROP_DATABASE_URL must be configured before running database migrations."
        )
    return database_url


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations without creating a database engine."""
    config.set_main_option("sqlalchemy.url", configured_database_url().replace("%", "%%"))
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations through an asynchronous SQLAlchemy engine."""
    config.set_main_option("sqlalchemy.url", configured_database_url().replace("%", "%%"))
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

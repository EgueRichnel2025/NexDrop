# NexDrop API

FastAPI control-plane service for NexDrop. The API coordinates identity, devices,
signaling, plans, and transfer metadata. File bytes are intended to travel directly
between peers whenever possible; this service is not the default file-transfer path.

## Requirements

- Python 3.12
- uv 0.12+
- Docker Desktop with Docker Compose
- PostgreSQL 17 (provided locally through Compose)

## Setup

From this directory, configure the uv cache on the D: drive in Git Bash:

```bash
export UV_CACHE_DIR='D:/DevTools/uv-cache'
uv sync --locked
cp .env.example .env
```

Generate a strong local database password:

```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

Set `NEXDROP_POSTGRES_PASSWORD` in `.env` to that value. Set the password
inside `NEXDROP_DATABASE_URL` to the exact same value. Do not commit `.env`
or share its contents.

Start the dedicated PostgreSQL 17 instance:

```bash
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d --wait
docker compose --env-file .env ps
```

The database is named `nexdrop`, the application role is `nexdrop`, and the
database is exposed only on `127.0.0.1:5434`. Data is persisted in the named
Docker volume `nexdrop_postgres_data`. The Compose service has a PostgreSQL
readiness health check. It does not reuse or modify another project's containers,
volumes, or host PostgreSQL service.

To stop the database without deleting its data:

```bash
docker compose --env-file .env stop
```

To start it again:

```bash
docker compose --env-file .env start
```

Do not use `docker compose down -v` unless you intentionally want to delete
the NexDrop database volume and all its data.

## Run

Start the API through the platform-aware entry point:

```bash
uv run python -m nexdrop_api.serve
```

The entry point configures the Windows asyncio Selector policy before Uvicorn
creates its event loop and uses Uvicorn's `loop="none"` mode so that policy is
not overridden by Uvicorn's default Windows Proactor factory. The development
server starts with reload enabled by default. Set `NEXDROP_SERVER_RELOAD=false`
for a non-reloading process. Do not use the raw `uvicorn nexdrop_api.main:app`
CLI command on Windows with the asynchronous Psycopg driver.

- GET /api/v1/health/live checks only that the API process is responding.
- GET /api/v1/health/ready performs a real `SELECT 1` check against PostgreSQL
  and returns HTTP 503 when the database is not configured or unavailable.

Alembic applies the same Selector policy before starting its asynchronous
migration runner.

## Database migrations

Alembic is configured for SQLAlchemy's asynchronous Psycopg driver. The initial
revision `3e98c6e8eb34` establishes migration version tracking only; it intentionally
creates no business tables. Domain models and their schema will be introduced by
subsequent, independently reviewable revisions.

With PostgreSQL running and `NEXDROP_DATABASE_URL` configured:

```bash
uv run alembic current
uv run alembic heads
uv run alembic upgrade head
```

## Quality checks

```bash
uv lock --check
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall src tests
uv run alembic heads
uv tree
```

## Configuration

All application settings use the `NEXDROP_` environment-variable prefix.
A local `.env` file is loaded for development; `.env.example` documents the
initial settings. CORS origins are explicit and credentials are disabled until
a concrete authentication model requires otherwise.

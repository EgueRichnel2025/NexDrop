# NexDrop API

FastAPI control-plane service for NexDrop. The API coordinates identity, devices,
signaling, plans, and transfer metadata. File bytes are intended to travel directly
between peers whenever possible; this service is not the default file-transfer path.

## Requirements

- Python 3.12
- uv 0.12+
- PostgreSQL for database-backed operations (not required for liveness or unit tests)

## Setup

From this directory, configure the uv cache on the D: drive in Git Bash:

```bash
export UV_CACHE_DIR='D:/DevTools/uv-cache'
cp .env.example .env
uv sync --locked
```

Edit .env and set NEXDROP_DATABASE_URL to a PostgreSQL database you control.
Never commit .env or real credentials.

## Run

```bash
uv run uvicorn nexdrop_api.main:app --host 127.0.0.1 --port 8000 --reload
```

- GET /api/v1/health/live checks only that the API process is responding.
- GET /api/v1/health/ready checks PostgreSQL with SELECT 1 and returns HTTP 503
  when the database is not configured or unavailable.

The application does not connect to PostgreSQL during import or startup. Database
connections are opened only when a database-backed dependency or readiness probe runs.

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

## Database migrations

Alembic is configured for SQLAlchemy's asynchronous Psycopg driver. No business
tables are defined in this foundation phase. Set NEXDROP_DATABASE_URL before
generating or applying migrations that require a live database.

## Configuration

All application settings use the NEXDROP_ environment-variable prefix.
A local .env file is loaded for development; .env.example documents the initial
settings. CORS origins are explicit and credentials are disabled until a concrete
authentication model requires otherwise.

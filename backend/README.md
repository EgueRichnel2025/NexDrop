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

Alembic is configured for SQLAlchemy's asynchronous Psycopg driver. The current
schema contains 13 business tables covering users, devices, sessions, transfers,
participants, invitations, audit events, plans, subscriptions, payments, and usage.

Applied revisions:

- `3e98c6e8eb34` — initial migration-version checkpoint.
- `8d9e28ddd1c7` — initial business schema and the Free plan seed (10,000,000,000 bytes per Internet transfer).
- `041602a30cb7` — transfer-size, timestamp, recipient-redemption, and same-session refresh-token invariants.

With PostgreSQL running and `NEXDROP_DATABASE_URL` configured:

```bash
uv run alembic current
uv run alembic heads
uv run alembic upgrade head
uv run alembic check
```

## Tests and quality checks

The ordinary unit/API tests run with `uv run pytest -q`. PostgreSQL integration tests
also run when `NEXDROP_TEST_DATABASE_URL` points to the separate, migrated `nexdrop_test`
database. Never point this variable at the development database. Each constraint test
uses a rollback-only transaction; the explicit two-session concurrency test cleans up
its isolated records.

Example Git Bash setup after creating and migrating the dedicated test database:

```bash
export NEXDROP_TEST_DATABASE_URL="$(uv run python - <<'PY'
from sqlalchemy.engine import make_url
from nexdrop_api.core.config import get_settings
url = get_settings().database_url
if url is None:
    raise SystemExit("NEXDROP_DATABASE_URL is not configured")
print(make_url(url).set(database="nexdrop_test").render_as_string(hide_password=False))
PY
)"
uv run pytest -q
```

Run the complete quality checks with:

```bash
uv lock --check
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall src tests migrations
uv run alembic heads
uv run alembic check
uv tree
```

## Configuration

All application settings use the `NEXDROP_` environment-variable prefix.
A local `.env` file is loaded for development; `.env.example` documents the
initial settings. CORS origins are explicit and credentials are disabled until
a concrete authentication model requires otherwise.

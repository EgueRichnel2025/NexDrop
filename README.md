# NexDrop

**Transfer without limits.**

NexDrop is a Windows-first desktop application for transferring files and folders between computers. It is being designed for direct local-network transfers and secure Internet transfers, with a relay used only when a direct peer connection is unavailable.

> Local first. Cloud when necessary.

## Product direction

- Send one file, multiple files, or complete folders.
- Discover nearby computers and transfer directly over a local network.
- No account required for LAN transfers.
- Internet transfers with account-based identity and plan enforcement.
- Receiver confirmation before incoming files are accepted.
- Chunked streaming, integrity verification, and interruption recovery.
- French and English interface; light and dark themes.
- Windows first, with macOS and Linux planned for later releases.

## Technology

| Area | Technology |
|---|---|
| Desktop shell | Tauri 2 |
| Frontend | React + TypeScript |
| Frontend tooling | Vite + pnpm |
| Native transfer engine | Rust |
| Online API | Python + FastAPI |
| Database | PostgreSQL |
| Local backend environment | Docker Compose |

The API is the control plane. File data should travel directly between peers whenever possible. A relay is a fallback data-plane component and must only forward encrypted content.

## Current development status

The repository contains the Tauri/React/Rust desktop foundation, initial architecture and roadmap documentation, and the first FastAPI server-backend foundation.

The backend includes isolated Python dependency management with uv, validated settings, asynchronous SQLAlchemy/Psycopg connectivity, a Windows-compatible event-loop policy for the async driver, Docker Compose PostgreSQL 17, an Alembic migration baseline, and tested liveness/readiness endpoints.

The PostgreSQL service is isolated from other local projects, binds only to 127.0.0.1:5434, and stores its data in the persistent `nexdrop_postgres_data` Docker volume. Local credentials are generated into the ignored `backend/.env` file.

The following are **not implemented yet**: account authentication, user/device management, transfer signaling, persistent business models and business-schema migrations, quotas, subscriptions, billing, LAN discovery, the Rust transfer engine, direct Internet transport, and relay service.

See:
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Backend development guide](backend/README.md)

## Development prerequisites

For the current Windows development target:

- Windows 11 x64
- Node.js compatible with the versions declared by the project dependencies
- pnpm
- Rust stable with the MSVC x64 target
- Visual Studio C++ Build Tools and Windows SDK
- WebView2 Runtime
- Python 3.12 and uv
- Docker Desktop with Docker Compose
- Git

## Desktop development

Install JavaScript dependencies:

~~~bash
pnpm install
~~~

Run the frontend development server:

~~~bash
pnpm dev
~~~

Run the desktop application:

~~~bash
pnpm tauri dev
~~~

Build the frontend:

~~~bash
pnpm build
~~~

Check the Rust/Tauri application:

~~~bash
cargo check --manifest-path src-tauri/Cargo.toml
~~~

On Windows, run Cargo commands from a Visual Studio Developer Command Prompt (or another shell where the MSVC compiler and linker are available).

## Backend development

From Git Bash, configure the uv cache on D: and synchronize the isolated environment:

~~~bash
cd /d/Projet/NexDrop/backend
export UV_CACHE_DIR='D:/DevTools/uv-cache'
uv sync --locked
~~~

Follow [backend/README.md](backend/README.md) to generate local database credentials and start the isolated PostgreSQL service before running the API.

Start the API:

~~~bash
uv run python -m nexdrop_api.serve
~~~

Health endpoints:
- GET http://127.0.0.1:8765/api/v1/health/live
- GET http://127.0.0.1:8765/api/v1/health/ready

The liveness endpoint does not require PostgreSQL. Readiness performs a real SELECT 1 check and returns HTTP 503 if PostgreSQL is not configured or unavailable.

## Repository structure

~~~text
.
├── backend/              # FastAPI control-plane service
├── docs/                 # Architecture and product roadmap
├── public/               # Static frontend assets
├── src/                  # React + TypeScript frontend
├── src-tauri/            # Tauri application and Rust core
├── package.json
├── pnpm-lock.yaml
└── vite.config.ts
~~~

## Engineering principles

- Keep the transfer engine independent from the UI.
- Never buffer an entire large file in memory.
- Validate all peer-provided paths and metadata.
- Treat receiver consent and end-to-end encryption as core requirements.
- Keep native permissions narrow and explicit.
- Add tests with each meaningful unit of behavior.
- Commit verified, coherent changes; do not create artificial commits to inflate activity.

## License

The project license has not yet been selected. Until a license is added, all rights are reserved by the copyright holder.

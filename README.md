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

The repository currently contains the Tauri/React/Rust application foundation and the initial architecture and roadmap documents. The actual transfer engine, LAN discovery, Internet transport, backend, and billing features have **not** been implemented yet.

See:
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)

## Development prerequisites

For the current Windows development target:

- Windows 11 x64
- Node.js compatible with the versions declared by the project dependencies
- pnpm
- Rust stable with the MSVC x64 target
- Visual Studio C++ Build Tools and Windows SDK
- WebView2 Runtime
- Git

## Getting started

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

## Repository structure

~~~text
.
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

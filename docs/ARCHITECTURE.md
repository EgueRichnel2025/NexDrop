# NexDrop — Architecture

**Product:** NexDrop
**Slogan:** Transfer without limits.
**Document status:** Initial architecture baseline
**Version:** 0.1.0

## 1. Product objective

NexDrop is a Windows-first desktop application for transferring individual files, multiple files, and complete folders between computers. It supports local-network transfers and transfers between computers connected through the Internet.

The product is designed around one rule:

> **Local first. Cloud when necessary.**

When two computers can communicate directly, file data should travel directly between them. NexDrop's backend coordinates identity, authorization, signaling, subscriptions, and transfer setup; it must not become the default data path.

## 2. Product principles

1. **Direct transfer first:** prefer a direct connection between sender and receiver.
2. **LAN without an account:** local discovery and local transfers must not require account creation.
3. **Receiver consent:** a transfer is never written to the receiver's chosen destination until the receiver accepts it.
4. **Bounded memory:** large files are streamed in chunks; the application must never load an entire transfer into RAM.
5. **Recoverability:** interruption must not silently corrupt a transfer; supported transfers must be resumable.
6. **Verifiable integrity:** successful completion requires integrity verification.
7. **Least privilege:** the frontend receives only the native capabilities it needs.
8. **Honest product limits:** Free/Pro limits are enforced by the trusted service for Internet transfers, not by a UI-only counter.
9. **Observable behavior:** transfer states, failures, retries, and progress must be explicit and testable.

## 3. Target platforms and technology

### Desktop application

| Layer | Technology | Responsibility |
|---|---|---|
| Desktop shell | Tauri 2 | Native window, application lifecycle, secure bridge |
| User interface | React + TypeScript | Screens, interaction, accessibility, localization |
| Build tooling | Vite + pnpm | Frontend development and production assets |
| Native core | Rust | Filesystem, transfer engine, networking, hashing, persistence |
| Windows toolchain | MSVC x64 + Windows SDK | Native Windows compilation |

Windows is the first supported desktop target. macOS and Linux are future targets and must not dictate premature abstractions that complicate the Windows release.

### Online services

| Service | Technology | Responsibility |
|---|---|---|
| API | Python + FastAPI | Authentication, devices, signaling, plans, quota, billing |
| Database | PostgreSQL | Accounts, devices, subscriptions, transfer metadata |
| Object/data relay | Dedicated relay service | Forward encrypted transfer streams only when direct connectivity fails |
| Deployment | Docker Compose initially | Reproducible local backend environment |

The relay is a separate data-plane component. It must not be confused with the API/control plane.

## 4. High-level architecture

~~~text
                         NEXDROP CONTROL PLANE
                +-----------------------------------+
                | FastAPI API                       |
                | Auth / Devices / Signaling        |
                | Plans / Quota / Billing           |
                +----------------+------------------+
                                 |
                         PostgreSQL
                                 |
                     connection negotiation
                                 |
          +----------------------+----------------------+
          |                                             |
     COMPUTER A                                    COMPUTER B
+-----------------------+                    +-----------------------+
| React + TypeScript UI |                    | React + TypeScript UI |
| Tauri 2               |                    | Tauri 2               |
| Rust transfer engine |<--- direct path --->| Rust transfer engine |
+-----------------------+                    +-----------------------+
          |                                             |
          +----------- encrypted relay fallback -------+
                              |
                    Opaque encrypted streams
~~~

The diagram is logical. The concrete Internet transport and NAT traversal mechanism must be selected and documented before implementing Internet transfers.

## 5. Desktop application boundaries

### Frontend

The React application is responsible for:
- navigation and screen composition;
- file/folder selection interaction;
- device and transfer presentation;
- confirmation dialogs;
- progress, pause, resume, cancel, and error states;
- French and English text;
- light and dark themes.

The frontend must not implement the transfer protocol, perform unbounded file reads, or make security decisions that belong to Rust or the backend.

### Tauri bridge

Tauri commands are typed, narrow entry points into native functionality. They should:
- validate all arguments;
- return structured success/error values;
- avoid long-running work on the UI thread;
- emit typed events for transfer progress and state changes;
- expose no arbitrary shell execution or unrestricted filesystem access.

Capabilities and permissions must be granted per feature and reviewed whenever a plugin or command is added.

### Rust core

The Rust core is responsible for:
- safe file and directory enumeration;
- source and destination validation;
- chunked reading and writing;
- transfer state machines;
- LAN discovery and peer connections;
- Internet transport adapters;
- pause/resume and recovery metadata;
- integrity verification;
- bounded concurrency and resource management.

The transfer engine should be a normal Rust library with unit and integration tests. Tauri commands are adapters around that library, not the place where the transfer algorithm lives.

## 6. Core Rust modules (planned)

The initial module boundaries are:

- **domain:** identifiers, transfer states, typed errors, plan-independent models;
- **filesystem:** file/folder enumeration and safe destination handling;
- **manifest:** transfer manifest, relative paths, sizes, timestamps, hashes;
- **chunking:** bounded chunk reader/writer and chunk metadata;
- **integrity:** per-chunk and whole-file verification;
- **transfer:** orchestration, state machine, cancellation, pause/resume;
- **transport:** transport traits and connection lifecycle;
- **lan:** local discovery and direct local connections;
- **internet:** signaling integration and direct peer connection;
- **relay:** encrypted stream relay fallback;
- **persistence:** local transfer history and resumable state;
- **tauri_commands:** thin command/event adapters.

These are target boundaries, not a claim that these modules already exist.

## 7. Control plane and data plane

### Control plane

The FastAPI service manages:
- account and session authentication for Internet transfers;
- device registration and revocation;
- connection signaling and short-lived connection tickets;
- plan and quota checks;
- subscription and payment records;
- transfer metadata needed for coordination;
- relay allocation and abuse controls.

### Data plane

The data plane carries file bytes:
- LAN: direct local connection;
- Internet: direct peer connection when possible;
- fallback: relay forwards end-to-end encrypted bytes.

The API must not proxy every Internet file transfer. A relay must not receive file-decryption keys or plaintext file content.

## 8. Planned backend boundaries

The API is versioned under **/api/v1**. Initial logical modules:

- auth
- users
- devices
- signaling
- transfers
- subscriptions
- plans
- billing
- notifications
- admin
- health

Initial persistent concepts include User, Device, Session, Transfer, TransferParticipant, Plan, Subscription, Payment, and TransferLink. The schema will be refined before database migrations are written.

## 9. Transfer lifecycle

A transfer should follow an explicit state machine:

~~~text
created
  -> awaiting_receiver
  -> accepted
  -> connecting
  -> transferring
  -> verifying
  -> complete
~~~

The exact states and allowed transitions will be formalized in the transfer protocol specification and implemented as typed Rust transitions.

## 10. Large files and folders

- Read and write bounded chunks; never buffer a whole file.
- Keep concurrency configurable and bounded by available resources.
- Persist enough state to resume safely after application restart.
- Verify that source files have not changed before resuming.
- Preserve relative folder structure.
- Reject path traversal, absolute paths in remote manifests, and unsafe destination paths.
- Avoid overwriting existing files without explicit receiver policy.
- Do not recompress already-compressed formats by default.
- Any compression must be optional, measured, and negotiated by both peers.

## 11. Plans and limits

Initial commercial direction:

- **LAN:** free and unlimited; no account required.
- **Internet Free:** maximum 10 GB per transfer.
- **Internet Pro:** higher limits and paid capabilities, defined by the billing policy.
- **Business:** later phase for teams, administration, and organization controls.

The API is authoritative for Internet quota and plan entitlements. The UI may display limits but cannot be the enforcement point.

## 12. Quality attributes

The implementation must be evaluated for:
- correctness and integrity;
- transfer throughput and latency;
- bounded RAM use for large transfers;
- recovery after interruption;
- network changes and unstable connections;
- security and privacy;
- accessibility and localization;
- maintainability and testability;
- Windows installation and update behavior.

## 13. Architecture decisions still requiring an ADR

The following decisions must be made with a short Architecture Decision Record before implementation:
1. Internet transport and NAT traversal (for example, WebRTC-based transport versus QUIC plus a separately designed traversal strategy).
2. LAN discovery mechanism and fallback behavior.
3. Cryptographic handshake and peer identity model.
4. Local persistence format and retention policy.
5. Relay protocol, capacity model, and abuse controls.
6. Payment provider and subscription lifecycle.

No transport or cryptographic protocol should be invented ad hoc inside a feature implementation.

# NexDrop — Product and Engineering Roadmap

**Status:** Initial roadmap
**Release direction:** Windows first, LAN-first MVP, Internet connectivity after local transfer reliability.

This roadmap is organized around verifiable outcomes. A phase is not complete merely because code has been written: its tests, build, and acceptance criteria must pass.

## Phase 0 — Repository and environment baseline

- [x] Create the NexDrop Git repository and connect the GitHub remote.
- [x] Initialize the Tauri 2 + React + TypeScript application.
- [x] Configure pnpm and place its package store on the D: drive.
- [x] Install the Rust MSVC toolchain.
- [x] Verify the frontend production build.
- [x] Verify native Rust/Tauri dependencies with cargo check.
- [ ] Replace the starter template identity and documentation.
- [x] Establish the first reviewed architecture/documentation commits.

**Exit criteria:** reproducible frontend and native checks on the Windows development machine; generated files are correctly ignored; project identity is consistent.

## Phase 1 — Architecture and engineering standards

- [ ] Finalize the architecture and module boundaries.
- [ ] Document the transfer state machine and manifest format.
- [ ] Select and record LAN discovery and Internet transport decisions.
- [ ] Define security boundaries and threat assumptions.
- [ ] Define error conventions, logging, testing, and commit practices.

**Exit criteria:** no unresolved protocol decision is hidden inside implementation work.

## Phase 2 — Desktop foundation and design system

- [ ] Replace the starter screen with NexDrop's application shell.
- [ ] Establish design tokens for color, spacing, typography, radius, and motion.
- [ ] Implement light and dark themes.
- [ ] Establish French and English localization.
- [ ] Build accessible navigation, dialogs, notifications, and empty states.
- [ ] Define typed frontend/native contracts.

**Exit criteria:** the desktop shell builds cleanly and has no transfer behavior implemented with fake data presented as real functionality.

## Phase 3 — Rust transfer engine foundation

- [ ] Create independently testable Rust domain modules.
- [ ] Implement file and folder manifests.
- [ ] Implement bounded chunk reading and writing.
- [ ] Implement structured transfer errors and state transitions.
- [ ] Implement integrity verification.
- [ ] Add unit and integration tests for large files and folder structures.

**Exit criteria:** Rust tests prove bounded-memory file processing, manifest correctness, and integrity behavior without requiring the UI.

## Phase 4 — LAN discovery and local transfer

- [ ] Implement local device discovery.
- [ ] Present discovered devices and a manual connection code.
- [ ] Add QR-based connection information.
- [ ] Require receiver confirmation.
- [ ] Establish an authenticated local peer connection.
- [ ] Transfer files, multiple files, and folders directly over LAN.
- [ ] Display real progress, speed, and transfer state.

**Exit criteria:** two Windows computers can discover one another, authorize a transfer, and transfer files/folders directly on a local network.

## Phase 5 — Reliability and recovery

- [ ] Add pause, resume, and cancellation.
- [ ] Persist resumable transfer metadata.
- [ ] Resume after app restart and temporary network interruption.
- [ ] Detect source-file changes before resuming.
- [ ] Verify each completed file and the complete transfer.
- [ ] Test collisions, insufficient disk space, permissions, and partial writes.

**Exit criteria:** interruption does not produce a false success or silently corrupted output.

## Phase 6 — Internet identity and signaling

- [x] Establish the FastAPI application foundation and versioned health API.
- [ ] Implement the remaining versioned API domain modules.
- [ ] Add PostgreSQL business models, migrations, and persistence.
- [ ] Implement account/session authentication.
- [ ] Register and revoke devices.
- [ ] Implement short-lived signaling and connection tickets.
- [ ] Add security, rate-limit, and abuse protections.

**Exit criteria:** two authenticated devices can negotiate a connection without sending file data through the API.

## Phase 7 — Direct Internet transfer and relay fallback

- [ ] Implement the selected direct peer transport.
- [ ] Test NAT and firewall conditions.
- [ ] Add relay fallback when direct connectivity fails.
- [ ] Ensure relay forwarding handles ciphertext only.
- [ ] Integrate Internet pause/resume and integrity checks.
- [ ] Test network switching and unstable connectivity.

**Exit criteria:** Internet transfers use a direct path whenever possible and a secure relay only when necessary.

## Phase 8 — Free and Pro plans

- [ ] Define plan entitlements and quota semantics.
- [ ] Enforce the 10 GB Free per-transfer Internet limit server-side.
- [ ] Integrate subscription and payment lifecycle.
- [ ] Add clear upgrade and quota messaging.
- [ ] Add auditability for quota and billing events.

**Exit criteria:** plan enforcement is authoritative, testable, and cannot be bypassed by changing frontend state.

## Phase 9 — Product completeness

- [ ] Transfer history and detailed transfer records.
- [ ] Trusted/known device management.
- [ ] Notifications and useful failure recovery guidance.
- [ ] Transfer links/codes with expiration and receiver consent.
- [ ] Windows Explorer context-menu integration.
- [ ] Accessibility and localization review.

**Exit criteria:** the primary workflows are understandable and recoverable without developer tools.

## Phase 10 — Security, performance, and release

- [ ] Threat-model review and security testing.
- [ ] Dependency and vulnerability review.
- [ ] Load, throughput, and large-file memory tests.
- [ ] Windows installer and signed-release preparation.
- [ ] Upgrade, uninstall, and data-retention tests.
- [ ] User documentation and support diagnostics.

**Exit criteria:** release candidate passes the defined acceptance suite on supported Windows systems.

## Later releases

- macOS and Linux desktop support.
- Business plans, team administration, and organization policies.
- Additional transfer workflows based on validated user demand.
- Mobile companion applications only after the desktop product is stable.

## Development discipline

For every phase:
1. Inspect the current implementation before editing.
2. State the objective and expected changes.
3. Make a small, coherent change.
4. Run the narrow tests, then relevant full checks.
5. Review git diff and git status.
6. Commit only verified work with a descriptive message.
7. Update this roadmap when a milestone genuinely passes.

Never create empty commits or split one trivial change into artificial commits just to increase contribution counts.

# Development snapshot

This is an unfinished Phase 1 development snapshot, exported so it can be opened locally in VS Code. Phase 2 is paused until the owner confirms Phase 1 is verified.

Verified in the cloud workspace: 42 API/service tests, including ten fixture-backed queued URL extractions, repeated URL deduplication, local TXT/PDF/DOCX parsing, fact review, task handling, read-only Sheet import fixtures, OAuth permission/state checks, and checksum-verified database/storage backup restoration. The production frontend build and desktop/mobile browser smoke tests pass for direct dashboard access, reload/reopen, server-only credentials and local origin guards, job CRUD/history, profile/fact review and deadlines. CV review, backup, OAuth and extraction UI flows and the full new design requirements still need browser verification.

Google OAuth is not connected. The only requested scope is `https://www.googleapis.com/auth/spreadsheets.readonly`. The original tracker is blocked. Sheet write-back is disabled at the API, worker, sync service and HTTP client. Tests use synthetic fixtures, not the owner's Sheet or real portals. A development-copy import has not been verified.

## Run on macOS

Requires Python 3.12+, uv, Node.js 24 and npm. From the project directory:

```sh
python3 scripts/init_local.py
cd apps/api
uv sync --frozen
uv run alembic upgrade head
cd ../web
npm ci
cd ../..
python3 scripts/dev.py
```

Open `http://127.0.0.1:3000` on the same machine: the dashboard opens directly with no unlock page, token entry or lock/sign-out button. The launcher starts the web app, API and worker on localhost and keeps `APP_ACCESS_TOKEN` server-side. Refreshing or reopening the browser requires no extra steps. Press Ctrl+C to stop. Do not expose the ports publicly.

Never commit `.env`, `.local/`, or `storage/`. No credentials or owner data are included in this snapshot. `scripts/init_local.py` generates a fresh token and local encryption key without printing either.

The existing README and decision record describe the earlier foundation. Treat this status file as the current implementation/validation summary until those documents and the expanded browser tests are updated. The product requirements remain in `docs/SPEC.md` and coding instructions in `AGENTS.md`.

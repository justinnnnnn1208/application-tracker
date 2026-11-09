# Application tracker

A single-user, local-first workspace for UK graduate job opportunities. Phase 1 is incomplete; Phase 2 is paused until the owner explicitly confirms Phase 1 is verified. Application submission and Google Sheet writes are disabled.

## Start here

| Read | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Agent rules, safety and mandatory session-start reading order |
| [Project context](docs/context/PROJECT.md) | Stable purpose, agent role and owner working preferences |
| [Product spec](docs/SPEC.md) | Requirements, phases and acceptance criteria |
| [Current status](STATUS.md) | What is implemented, tested, unverified or blocked |
| [Latest handover](docs/HANDOVER.md) | Exact unfinished work and where the next session should resume |
| [Setup](docs/SETUP.md) | Mac run commands, verification, read-only Google setup and backup/restore |

[CLAUDE.md](CLAUDE.md) directs Claude Code to the same shared instructions. No plugin is required. An arbitrary Markdown folder is not guaranteed to be read automatically; agents must follow the linked entry-point instructions or be explicitly asked to read AGENTS.md.

## Run locally on macOS

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

Open `http://127.0.0.1:3000` on the same computer. The dashboard opens directly. The API token stays server-side; no unlock page or token entry is needed. Keep the terminal open and use Control+C to stop. The launcher starts the web app, API and worker and loads the private root `.env` literally; exported environment variables take precedence.

For later starts, run `python3 scripts/dev.py` from the root. For updates, stop the app and use `git pull --ff-only origin dev/phase-1`, preserving any local changes. See [SETUP.md](docs/SETUP.md) for dependency/migration refreshes and troubleshooting.

## Current capabilities

Jobs/profile/fact management, manual and queued URL intake, canonical-URL deduplication, status history, dashboard/deadlines, a separate worker, local CV parsing/review, read-only Sheets OAuth/import code, and checksum-verified backup/restore are implemented to varying levels of verification. [STATUS.md](STATUS.md) records the evidence and limits. An unfinished UI redesign is local and not published.

Google is not connected or verified against the owner's development copy. The original tracker is blocked; broad write scope and Sheet mutations are disabled. See [Google setup](docs/SETUP.md#google-cloud-read-only-development-copy-setup) for the exact read-only OAuth scope, redirect URI and private JSON-file location. Do not send credentials through chat.

Matching, application preparation, browser prefill and submission are later-phase work, not available features. The current DB restricts application statuses and sponsorship so neither confirmed submission nor sponsored-role claims can be set without the later evidence workflow.

## Privacy and storage

Keep both ports (UI 3000, API 8000) on localhost. The local web proxy enforces loopback hosts and same-origin writes; direct API requests still require a token. This trusts users of the local machine and must not be exposed publicly.

`.env`, `.local/`, `storage/` and generated dependencies are ignored. CVs, profile facts and the SQLite database are local; they are not encrypted by default. OAuth tokens are Fernet-encrypted, with the key in private configuration. Keep that key separately so backups remain recoverable. Never store credentials, CV text or legal declarations in tracked context documents.

No real applicant/job data or sample opportunities are seeded. Facts need owner review; legal declarations are fixed owner-confirmed values and are never LLM-generated. Submission is off. All fetched content is untrusted data.

## Verification and continuity

Checks and their working directories are in [SETUP.md](docs/SETUP.md#useful-verification-commands). Browser checks use disposable DB/storage and loopback test ports, never owner data. Historic passing checks do not establish that a later unfinished checkout works.

At the end of a session, update [STATUS.md](STATUS.md) and [HANDOVER.md](docs/HANDOVER.md), using the [session template](docs/templates/SESSION_HANDOVER.md). Record actual commands/outcomes, owner inputs, phase gates and uncommitted work. Commit/push only the completed, checked scope to `dev/phase-1`; leave unrelated unfinished work intact.

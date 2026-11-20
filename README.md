# Application tracker

A single-user, local-first workspace for UK graduate job opportunities. Phase 2 is in progress. Phase 1 was accepted for progression with live single-cell write verification and Mac operational checks deferred. Application submission is unavailable; Google Sheets remains read-only by default.

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

Requires Python 3.12+, uv, Node.js 24 and npm. From the project directory, run one command at a time and stop if a command fails:

```sh
python3 scripts/init_local.py
cd apps/api
uv sync --frozen
cd ../web
npm ci
cd ../..
python3 scripts/dev.py --migrate
```

Open `http://127.0.0.1:3000` on the same computer. The dashboard opens directly. The API token stays server-side; no unlock page or token entry is needed. Keep the terminal open and use Control+C to stop. The launcher starts the web app, API and worker and loads the private root `.env` literally; exported environment variables take precedence.

For later starts, run `python3 scripts/dev.py` from the root. For updates, stop the app and use `git pull --ff-only origin dev/phase-1`, preserving any local changes, then `python3 scripts/dev.py --migrate` to verify a backup and apply migrations before starting. See [SETUP.md](docs/SETUP.md) for dependency/migration refreshes and troubleshooting.

## Current capabilities

Jobs/profile/fact management, manual and queued URL intake, canonical-URL deduplication, status history, dashboard/deadlines, a separate worker, local CV parsing/review, read-only-by-default Sheets OAuth/import and opt-in development-copy status writes, and checksum-verified backup/restore are implemented to varying levels of verification. [STATUS.md](STATUS.md) records the evidence and limits. The reference-inspired UI now uses Inter, a charcoal-grey layout with blue actions, compact URL intake, combined job filters/sorting, direct listing links, clearly labelled imported Sheet statuses and collapsible settings. Its production desktop/mobile smoke checks pass; remaining workflow and live integration limits are recorded in STATUS.md.

The owner confirmed Google connection and all 20 development-copy rows imported on their Mac. This cloud checkout has no access to that private OAuth session. The original tracker remains blocked; do not enable write access during current Phase 2 work. See [Google setup](docs/SETUP.md#google-cloud-read-only-development-copy-setup) for read-only OAuth and the private JSON-file location. Never send credentials through chat.

Phase 2 adds explicit public-board discovery, source-ID aliases/fuzzy review hints, explainable deterministic preference scores, current/stale batch ranking, manual Good/Poor feedback and weight controls. Sponsorship never filters or penalises a score. Optional local Ollama extracts source-quoted requirement candidates, and an owner-confirmed dated register CSV supplies a separate licence signal. Neither establishes personal/legal eligibility. Application preparation, browser prefill and submission remain later-phase work.

| Discovery source | Implemented / current evidence |
|---|---|
| Greenhouse | Public board; live disposable import/repeat preservation passed |
| Lever global/EU | Public board; synthetic contract/worker/browser tests; live unverified |
| Ashby | Listed public postings; synthetic tests; live unverified |
| SmartRecruiters | First 20 company postings plus detailed text; synthetic tests; live unverified |
| Reed | First 20 keyword matches plus detailed text; private API key required; synthetic tests; live unverified |

No automatic discovery schedule or sources are seeded. Add a source in Settings after reviewing terms and host access, enable manual imports, then inspect Background tasks and Jobs. See [setup](docs/SETUP.md) for each source and optional local model/register configuration. Actual Ollama quality, official register-file verification and independent multi-ATS evaluation remain outstanding; Phase 2 is not certified complete.

## Privacy and storage

Keep both ports (UI 3000, API 8000) on localhost. The local web proxy enforces loopback hosts and same-origin writes; direct API requests still require a token. This trusts users of the local machine and must not be exposed publicly.

`.env`, `.local/`, `storage/` and generated dependencies are ignored. CVs, profile facts and the SQLite database are local; they are not encrypted by default. OAuth tokens are Fernet-encrypted, with the key in private configuration. Keep that key separately so backups remain recoverable. Never store credentials, CV text or legal declarations in tracked context documents.

No real applicant/job data or sample opportunities are seeded. Facts need owner review; legal declarations are fixed owner-confirmed values and are never LLM-generated. Submission is off. All fetched content is untrusted data.

## Verification and continuity

Checks and their working directories are in [SETUP.md](docs/SETUP.md#useful-verification-commands). Browser checks use disposable DB/storage and loopback test ports, never owner data. Historic passing checks do not establish that a later unfinished checkout works.

At the end of a session, update [STATUS.md](STATUS.md) and [HANDOVER.md](docs/HANDOVER.md), using the [session template](docs/templates/SESSION_HANDOVER.md). Record actual commands/outcomes, owner inputs, phase gates and uncommitted work. Commit/push only the completed, checked scope to `dev/phase-1`; leave unrelated unfinished work intact.

Existing Sheet imports backfill missing literal role/location fields from stored Notes at API startup. Job details label Notes summaries when no full vacancy text exists. Pull/restart applies the repair locally; no re-entry of the 20 rows or new Google permission is needed. Source-grounded model extraction requires actual vacancy text and excludes Notes.

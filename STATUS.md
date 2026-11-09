# Current project status

Reviewed: 9 November 2026 (Europe/London). This records the current checked UI redesign and the remaining Phase 1 integration limits.

**Phase 1: incomplete, roughly 70% verified. Phase 2: paused until the owner explicitly confirms Phase 1 is verified.** The percentage is a rough communication aid; only the acceptance criteria establish completion.

Start with [AGENTS.md](AGENTS.md), [stable context](docs/context/PROJECT.md), [SPEC.md](docs/SPEC.md) and the [latest handover](docs/HANDOVER.md). Runtime and Google configuration instructions are in [SETUP.md](docs/SETUP.md).

## Published application baseline

The previous reference-inspired Phase 1 UI was published in [`d20a19e`](https://github.com/justinnnnnn1208/application-tracker/commit/d20a19e0c135fbb74e11130d315368560b8c7d27) on `dev/phase-1`; the full local SHA matched the remote ref. It builds on `1c7c8e2` (direct dashboard access) and the shared context documentation. No backend or dependency changes were needed for the current theme/reminder delivery. See [HANDOVER.md](docs/HANDOVER.md) for the checked scope and delivery record.

The published app opens directly to the dashboard, including after browser refresh/reopen and web-server restart. There is no unlock page or lock/sign-out control. The API token remains server-side, the proxy rejects non-local/cross-origin requests, and direct backend requests remain authenticated. Services bind to localhost.

The owner has run the app on a Mac in VS Code. Cloud checks are not a substitute for verifying new changes on that laptop.

## Implemented capabilities and limits

| Capability | Current evidence and limits |
|---|---|
| Jobs, profile/facts, manual intake, dedupe, status history and deadlines | API tests and core browser smoke tests passed for the published baseline |
| Queued URL extraction and a separate worker | Ten synthetic fixture URLs exercised API → task → worker → extractor → database; live job pages not verified |
| Local CV upload/parsing and fact review | TXT/PDF/DOCX service tests and explicit fact-review tests passed; actual-worker TXT upload, correction, explicit confirmation and byte-identical download now pass in the browser |
| Backup/restore and overdue scheduling | Database/files/checksums restored in tests; overdue work enqueued once; settings-triggered backup and CLI restore now pass end to end with disposable data |
| Google OAuth and import | Read-only scope, state/PKCE/encryption and synthetic Sheet preservation tests passed; no live Google connection or development-copy import verified |
| Sheet writes, application submission and later phases | Disabled; no approval to enable them |
| UI redesign using the owner's references | Inter/blue charcoal-grey dashboard, 220px sidebar, compact URL intake, real counts, neutral Unverified labels, job filters/sorting and native collapsible settings/tasks; production browser checks passed at 1440px, 390px and 320px |

## Phase 1 acceptance criteria

PASSED below means the stated controlled check passed in the current 42-test run. It does not mean real-site, development-copy or whole-phase acceptance has been established.

| Criterion from SPEC.md | Result | Evidence | Remaining limit |
|---|---|---|---|
| Ten pasted URLs create ten correct job rows | PASSED — controlled fixtures | `test_ten_queued_url_extractions_and_repaste_dedupe` in [test_workflows.py](apps/api/tests/test_workflows.py) checks the real queue/worker/extractor/DB path with a mocked external fetch | Ten live vacancy pages not tested |
| Re-pasting creates no duplicates | PASSED — controlled fixtures | Same test requeues all ten canonical URLs with tracking variants and checks stable IDs/count/history; manual dedupe also tested | Live source variations not tested |
| Sheet import preserves all rows | NOT TESTED on development copy | `test_readonly_import_preserves_all_rows_formulas_notes_and_prior_status` passed against a synthetic fixture, including incomplete rows | Requires owner-configured OAuth and the actual development copy |
| Status write changes only the target cell; formulas/formatting/notes preserved | NOT TESTED | Write operations are blocked at API, worker, sync service and HTTP client; blocking tests passed | Read-only import must be verified and the owner must separately approve writes before this acceptance check can run |
| Database and storage backup restores successfully | PASSED — disposable data | Backup/restore tests verify restored DB contents, exact file bytes, checksums, integrity and tamper rejection | Owner chooses a destination; operational restore should be verified on the laptop before relying on backups |
| Jobs default to UNVERIFIED unless supported by evidence | PASSED | API/database constraints, extraction defaults and non-inference tests in [test_tracker.py](apps/api/tests/test_tracker.py) and [test_workflows.py](apps/api/tests/test_workflows.py) | This slice stores only UNVERIFIED; automatic evidence assessment belongs to the gated later phase |

## Checks performed for this delivery

These checks were run on the redesigned UI/source in the cloud workspace using disposable data:

- `uv run --frozen pytest -q --tb=short` from `apps/api`: **42 passed**, one dependency deprecation warning.
- `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build` from `apps/web`: passed.
- `uv run --frozen --group browser python ../../scripts/smoke_browser.py` from `apps/api`: passed for direct dashboard, reload/reopen/server restart, credential/origin guards, manual job CRUD/history, profile/fact review, deadlines, combined filters, notes search, sorting, actual dashboard counts, neutral sponsorship labels, collapsible backup settings, visible mobile navigation and 44px enabled Dashboard controls at 320px. All pages fit the 390px viewport; desktop checks used 1440px. No console page errors were recorded.

The stylesheet uses the existing Inter package and blue `#2F5BEA`; 11 dark-theme normal-size text/background palette pairs passed a 4.5:1 contrast calculation. The charcoal Dashboard screenshot was visually inspected; responsive screenshots are retained only in ignored .local/. No new dependencies, components directory structure, backend services, matching or review queues were added. This is not a full accessibility certification. The expanded browser run now starts the real separate worker and verifies pasted fixture HTML extraction, TXT CV upload, editing and confirming a candidate, byte-identical CV download, saving a backup destination, requesting a restore-verified backup and running the CLI restore into a new folder. Restored jobs, reviewed facts and CV bytes are checked. PDF/DOCX have service coverage, not full browser coverage. OAuth/import still requires live development-copy verification.

## Owner inputs and remaining work

- The owner selected macOS/browser reminders. Optional Notification API reminders are implemented. Browser checks with a simulated Notification API passed for explicit opt-in, the correct due job and avoiding repeated reminders when paused/re-enabled. Actual macOS delivery still needs owner verification with browser/OS permission.
- Google: development-copy spreadsheet ID, exact tab name and header-row number; OAuth setup described in [SETUP.md](docs/SETUP.md). Column headers have already been supplied—do not ask for them again.
- Extraction provider/model choice before hosted fallback is enabled. Personal-data use of hosted models still needs explicit approval.
- UI references were supplied in conversation; no `docs/design/dashboard.png` asset is present in the repository.
- The current UI redesign is complete. Next Phase 1 work is an owner-configured read-only development-copy import and a Mac notification delivery check. Do not start matching/Phase 2 from the rough progress percentage.

No credentials, CV text, legal declarations or owner database contents belong in this status file. See [HANDOVER.md](docs/HANDOVER.md) for exact unfinished paths and resumption steps.

Latest delivery: charcoal theme and expanded real-worker browser verification are checked locally; publication is recorded in HANDOVER.md. New commits use the owner-provided Git identity, configured locally rather than stored in project Markdown.

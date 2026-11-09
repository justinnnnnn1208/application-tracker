# Current project status

Reviewed: 9 November 2026 (Europe/London). This is an evidence summary, not a claim that the entire checkout has passed all checks today.

**Phase 1: incomplete, roughly 60% verified. Phase 2: paused until the owner explicitly confirms Phase 1 is verified.** The percentage is a rough communication aid; only the acceptance criteria establish completion.

Start with [AGENTS.md](AGENTS.md), [stable context](docs/context/PROJECT.md), [SPEC.md](docs/SPEC.md) and the [latest handover](docs/HANDOVER.md). Runtime and Google configuration instructions are in [SETUP.md](docs/SETUP.md).

## Published application baseline

Last published application change: [`1c7c8e2`](https://github.com/justinnnnnn1208/application-tracker/commit/1c7c8e29cdaf674290c71825c88493449ef91049), on `dev/phase-1`. Later documentation commits do not imply a newer tested application build.

The published app opens directly to the dashboard, including after browser refresh/reopen and web-server restart. There is no unlock page or lock/sign-out control. The API token remains server-side, the proxy rejects non-local/cross-origin requests, and direct backend requests remain authenticated. Services bind to localhost.

The owner has run the app on a Mac in VS Code. Cloud checks are not a substitute for verifying new changes on that laptop.

## Implemented capabilities and limits

| Capability | Current evidence and limits |
|---|---|
| Jobs, profile/facts, manual intake, dedupe, status history and deadlines | API tests and core browser smoke tests passed for the published baseline |
| Queued URL extraction and a separate worker | Ten synthetic fixture URLs exercised API → task → worker → extractor → database; live job pages not verified |
| Local CV upload/parsing and fact review | TXT/PDF/DOCX service tests and explicit fact-review tests passed; full CV upload browser workflow still needs verification |
| Backup/restore and overdue scheduling | Database/files/checksums restored in tests; overdue work enqueued once; full settings browser workflow not verified |
| Google OAuth and import | Read-only scope, state/PKCE/encryption and synthetic Sheet preservation tests passed; no live Google connection or development-copy import verified |
| Sheet writes, application submission and later phases | Disabled; no approval to enable them |
| UI redesign using the owner's references | Paused, unfinished local edits; styling and browser verification pending; not published |

## Phase 1 acceptance criteria

PASSED below means the stated controlled check passed previously. It does not mean real-site, development-copy or whole-phase acceptance has been established.

| Criterion from SPEC.md | Result | Evidence | Remaining limit |
|---|---|---|---|
| Ten pasted URLs create ten correct job rows | PASSED — controlled fixtures | `test_ten_queued_url_extractions_and_repaste_dedupe` in [test_workflows.py](apps/api/tests/test_workflows.py) checks the real queue/worker/extractor/DB path with a mocked external fetch | Ten live vacancy pages not tested |
| Re-pasting creates no duplicates | PASSED — controlled fixtures | Same test requeues all ten canonical URLs with tracking variants and checks stable IDs/count/history; manual dedupe also tested | Live source variations not tested |
| Sheet import preserves all rows | NOT TESTED on development copy | `test_readonly_import_preserves_all_rows_formulas_notes_and_prior_status` passed against a synthetic fixture, including incomplete rows | Requires owner-configured OAuth and the actual development copy |
| Status write changes only the target cell; formulas/formatting/notes preserved | NOT TESTED | Write operations are blocked at API, worker, sync service and HTTP client; blocking tests passed | Read-only import must be verified and the owner must separately approve writes before this acceptance check can run |
| Database and storage backup restores successfully | PASSED — disposable data | Backup/restore tests verify restored DB contents, exact file bytes, checksums, integrity and tamper rejection | Owner chooses a destination; operational restore should be verified on the laptop before relying on backups |
| Jobs default to UNVERIFIED unless supported by evidence | PASSED | API/database constraints, extraction defaults and non-inference tests in [test_tracker.py](apps/api/tests/test_tracker.py) and [test_workflows.py](apps/api/tests/test_workflows.py) | This slice stores only UNVERIFIED; automatic evidence assessment belongs to the gated later phase |

## Recorded checks for the published baseline

These are previously recorded outcomes; the documentation/context task did not rerun them.

- `uv run --frozen pytest -q --tb=short` from `apps/api`: **42 passed**, one dependency deprecation warning.
- `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build` from `apps/web`: passed.
- `uv run --frozen --group browser python ../../scripts/smoke_browser.py` from `apps/api`: passed for direct dashboard, reload/reopen/server restart, credential/origin guards, manual job CRUD/history, profile/fact review, deadlines and desktop/mobile layout using disposable data.

The local paused UI redesign differs from this baseline. No successful build/browser result is claimed for those unfinished edits. Its changed headings and layout will also require checking/updating the browser smoke selectors. The full written design and all new workflow UI paths remain unverified.

## Owner inputs and remaining work

- Google: development-copy spreadsheet ID, exact tab name and header-row number; OAuth setup described in [SETUP.md](docs/SETUP.md). Column headers have already been supplied—do not ask for them again.
- Extraction provider/model choice before hosted fallback is enabled. Personal-data use of hosted models still needs explicit approval.
- UI references were supplied in conversation; no `docs/design/dashboard.png` asset is present in the repository.
- Finish the paused Phase 1 UI redesign and its tests only when that task is resumed. Do not start matching/Phase 2 from the rough progress percentage.

No credentials, CV text, legal declarations or owner database contents belong in this status file. See [HANDOVER.md](docs/HANDOVER.md) for exact unfinished paths and resumption steps.

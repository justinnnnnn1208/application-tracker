# Latest session handover

## Session

Reviewed: 9 November 2026 (Europe/London). Branch: `dev/phase-1`.

Latest request: read AGENTS.md/handover and work through tomorrow's task sheet. Preserve minimal structure, direct dashboard access, charcoal theme and owner Git authorship. Phase 2 remains paused. The owner supplied development-copy configuration, reported Google connected/all 20 jobs imported, and approved copy-only status writes. A later recommendation to defer live write verification was not explicitly accepted as revised Phase 1 scope.

Initial worktree contained the previous session's unfinished write-back integration, tests and direct listing links (10 modified files); preserved and completed rather than discarded. Last published baseline was `949ea62`. No owner data or local credentials were modified.

## Work completed

- Completed default-disabled copy-only status writes through API queue, worker, sync service and HTTP client. Only existing linked mapped status cells are written, RAW one cell per request. No appends or Notes/deadline/sponsorship writes. Original tracker stays blocked even if configured as the allowed write ID.
- Read-only import remains the default and scheduled behaviour. Private `SHEETS_WRITE_COPY_ID` opt-in selects broader OAuth scope; old readonly tokens can still import but cannot write. Renewed consent required; only read/write spreadsheet scopes accepted, no unrelated grants.
- Sync guards formulas, duplicate URLs, moved rows and changed targets. Uncertain write outcomes become NEEDS_INPUT; no automatic retries. Separate Google reads/writes are not atomic: avoid concurrent copy editing during the manual test.
- Direct Open listing links in job tables; visible original Sheet statuses in rows/details, an Applied-imported filter and Dashboard source count explanation. Confirmed Applied count stays zero; no APPLIED state or submission path added.
- Updated spec, setup, context and AGENTS authorization notes. No dependencies, migrations, services or directory abstractions added. Writes remain disabled unless owner explicitly configures them locally.

## Task sheet

| Order | Task | State / remaining action |
|---|---|---|
| 1 | Pull/start latest app | Delivery prepared here; owner runs Mac commands below after push. Cloud production app builds/runs. |
| 2 | Verify 20 imported jobs | PASSED by owner report; cloud cannot inspect private Mac data. Fixtures independently cover preservation. |
| 3 | Open listing links | PASSED in browser: correct href and safe new-tab attributes; real destination portals not opened. Owner can click actual imported listings. |
| 4 | Clarify imported Applied | IMPLEMENTED/TESTED: rows/details, dedicated filter, Dashboard explanation, no false confirmation. |
| 5 | Desktop reminders | PASSED with deterministic Notification fake (opt-in/dedupe); actual macOS delivery requires owner browser/OS permission and check. |
| 6 | Local backup/restore | PASSED with disposable real-worker UI backup and CLI restore, including exact CV bytes; owner chooses local directory and checks operational restore. |
| 7 | Sheets rollout | Default read-only preserved. Copy-only write implementation tested; live one-cell check requires private env setting and renewed OAuth consent (SETUP.md). Deferral is an option, not an accepted scope change yet. |
| 8 | Phase 1 review | PENDING: live write test or explicit accepted deferral, plus owner review of Mac checks. Do not claim fully complete. |
| 9 | Phase 2 | NOT STARTED: explicit owner progression approval required. |

## Phase 1 acceptance

| Criterion | Result | Verification / limit |
|---|---|---|
| 10 URLs create correct rows | PASSED — fixtures | Current real queue/worker/extractor/DB tests, with mocked external fetch; no live 10-page evaluation. |
| Re-pasting deduplicates | PASSED — fixtures | Tracking variants keep IDs/count/history. |
| Import preserves all rows | PASSED — owner report + fixtures | Owner reports 20 jobs and confirms matching data; synthetic incomplete-row/formula/Notes/source-status preservation tests. No independent private Google access here. |
| Status writes only one intended cell | NOT TESTED live | Exact single-cell RAW request, values/formulas/Notes preservation and guardrail tests pass; real copy/formatting test pending. |
| Backup restores | PASSED — disposable data | Checksums/integrity/tamper plus UI→worker backup→CLI restore of DB/facts/CV; operational Mac restore pending. |
| Defaults UNVERIFIED | PASSED | API/DB/extraction and neutral UI labels; Sheet Notes never infer YES. |

Rough Phase 1 progress: 80%; only acceptance evidence or an explicit revised scope can establish completion.

## Checks performed

- apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short`: **53 passed**, one existing dependency deprecation warning.
- apps/web: `npm run typecheck`; `NEXT_TELEMETRY_DISABLED=1 npm run build`: **PASSED**.
- apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen --group browser python ../../scripts/smoke_browser.py`: **PASSED** with final UI, separate disposable worker and data. Includes imported Applied labels/filter/count explanation and direct listing href checks, besides prior CRUD/security/CV/backup/reminder/mobile coverage.
- `git diff --check`: PASSED before staging. Jobs charcoal screenshot visually inspected; only ignored synthetic screenshots/logs retained.
- This delivery has no calls to real job portals, Google APIs or hosted LLMs. No automatic retries, write scopes or private env settings enabled in the owner/cloud runtime.

## Remaining work / resume

Read AGENTS.md and its context links, inspect Git state, then help the owner perform the Mac checks and choose live write verification or an explicit deferral. docs/SETUP.md documents the exact approved copy, case-sensitive tab/header settings, OAuth steps and one-cell test. Do not ask again for supplied headers, IDs or Google account details. Never request secrets, client JSON, callback URLs or tokens in chat.

Read-only remains the working default. Do not infer Phase 2 permission from implementing write-back or from the progress percentage. Full append/managed-field sync, live vacancy evaluation, PDF/DOCX browser upload, actual OS notification delivery and laptop operational restore are not verified by this session.

## Delivery and owner next step

Code/tests/docs are prepared for commit/push as one completed scope; publication is recorded in the follow-up delivery record and Git log. Generated next-env.d.ts drift is excluded. Owner Git identity remains configured; do not override with Codex or rewrite history.

On Mac, stop with Control+C and run from the project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py
```

No dependency or migration refresh needed. Open `http://127.0.0.1:3000`. Check Open listing and imported statuses, then test reminders and backup/restore. Keep current Google permission for read-only; only follow Optional approved status write-back in SETUP.md if choosing the live write test. No need to grant broader permission just to use the delivered UI.

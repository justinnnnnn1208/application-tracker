# Current project status

Reviewed: 9 November 2026 (Europe/London).

**Phase 1: incomplete, roughly 80% verified. Phase 2: paused pending explicit owner acceptance.** Percentages are rough communication aids, not acceptance criteria. Read AGENTS.md, docs/context/PROJECT.md, docs/SPEC.md and docs/HANDOVER.md before work.

## Latest checked work

- Job tables and details have direct Open listing links to the original application URL.
- Original Sheet statuses are visible separately from the app status. Applied history displays “Applied — imported from Sheet”, has a filter, and its count appears in the Dashboard Applied explanation. Imported claims never create confirmed APPLIED records; that count remains zero without evidence support.
- Approved status-only write-back is implemented, disabled by default. `SHEETS_WRITE_COPY_ID` must match the copy, and renewed OAuth consent must grant Sheets write permission. Original tracker access remains blocked; scheduled tasks remain read-only imports. No Notes, deadline, sponsorship or range writes, appends, submission functionality, dependency changes or migrations were added.
- The owner reported Google connected and all 20 development-copy jobs imported, then confirmed the requested preservation check and approved copy-only writes. This is owner-reported verification on the Mac, not independent cloud access to the private session.
- Native desktop reminders and local backup remain available. Cloud tests use disposable data; they do not prove Mac notification delivery or an operational restore on that laptop.

## Phase 1 acceptance criteria

| SPEC.md criterion | Result | Evidence and remaining limit |
|---|---|---|
| Ten pasted URLs create correct job rows | PASSED — controlled fixtures | Current API→queue→worker→extractor→DB tests verify 10 correct rows; browser checks pasted fixture HTML through a real worker. Live vacancy set untested. |
| Re-pasting creates no duplicates | PASSED — fixtures | Tracking URL variants preserve IDs/count/history in current suite. |
| Sheet import preserves all rows | PASSED — owner report and fixtures | Owner reports all 20 jobs and confirms matching data; synthetic tests preserve incomplete rows, formulas, Notes and source statuses. Actual Google task output not independently inspected here. |
| Status write changes only intended cell; formulas/formatting/Notes preserved | NOT TESTED on actual development copy | Single-cell RAW HTTP request, exact values/formula preservation, Notes conflict, duplicate/formula/moved-row/concurrent-cell guards, OAuth copy/scope gates and worker no-retry tests pass. Live formatting/preservation comparison still required. |
| Database/storage backup restores successfully | PASSED — disposable data | Service checksums/integrity/tamper tests and UI-requested backup→CLI restore verify jobs, reviewed fact and CV bytes in a new folder. Laptop operational restore untested. |
| Every job defaults UNVERIFIED | PASSED | Current API/DB/extraction tests; imported sponsorship claims remain Notes, not confirmed evidence. |

## Current verification

- In apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short`: **53 passed**, one existing Starlette/httpx deprecation warning.
- In apps/web: `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build`: **PASSED**.
- In apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen --group browser python ../../scripts/smoke_browser.py`: **PASSED** on final UI. Direct dashboard/reload/reopen/restart, server-only credentials, origin/auth guards, CRUD/history/profile/fact review, filter/search/sort/counts, Open listing href/rel, imported Applied labels/filter/count explanation, real-worker extraction, TXT CV edit/confirm/download, backup/CLI restore, opt-in Notification mock and 1440/390/320px layouts. No real Google or application portal calls.
- Notification mock proves opt-in and session dedupe; native macOS display, denied-permission path and day rollover remain untested here.
- Charcoal Jobs screenshot visually inspected; ignored .local artifacts contain only synthetic data. `git diff --check` passed before staging.

## Next steps and owner inputs

Follow the task sheet in docs/HANDOVER.md. On Mac pull/restart, verify listing links/imported labels, allow notifications and check a backup restore. Optional write setup and an exact one-cell acceptance procedure are in docs/SETUP.md. No credentials should be sent in chat.

The owner approved write implementation earlier. Keeping read-only and deferring live write-back was subsequently recommended but not explicitly accepted as a changed Phase 1 scope. Do not silently remove the criterion or start Phase 2. The owner must either verify the live write or explicitly accept the deferral, then authorise progression. Existing sync does not append new app jobs to Sheets or implement full managed-field synchronisation.

No owner data/configuration was reset or copied to tracked files. The current delivery will be committed/pushed using owner-configured Git authorship; see HANDOVER.md and Git log for publication.

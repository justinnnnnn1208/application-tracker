# Latest session handover

Reviewed: 9 November 2026 (UTC).

## Session

- Scope: continue Phase 1, change the bright UI to charcoal grey, and add owner-selected macOS/browser deadline reminders. Keep structure minimal.
- Branch: `dev/phase-1`; previous published baseline `67477cd`. The application delivery is published as `a625c01c4f4303fc5a944603b6fb997338069545`; its local SHA matched GitHub.
- Phase 1 remains incomplete (roughly 70%); Phase 2 requires explicit owner confirmation after Phase 1 verification.
- Initial worktree was clean. No owner data or pre-existing edits were changed.
- Owner requested future commits be attributed to their supplied Git identity. Local Git author configuration is set accordingly; do not override it with Codex. Existing history was not rewritten. Use the latest owner-authored commit as reference if configuration needs restoring, without copying the email into project context files.

## What changed

| Work | State | Files/evidence |
|---|---|---|
| Charcoal theme | TESTED | Existing globals.css updated in place: dark cards/inputs/native controls, readable grey text, blue actions. Existing layout/sizing preserved; no dependencies added. |
| Real-worker browser workflows | TESTED | smoke_browser.py now starts a separate disposable worker; verifies pasted fixture HTML extraction, TXT CV upload/edit/confirm, exact download bytes, settings-triggered backup and CLI restore into a fresh folder. Restored jobs/facts/CV bytes checked. |
| Desktop reminders | TESTED with simulated browser Notification API | tracker.tsx, no new service: explicit permission request on click, active jobs due within 7 UK-calendar days, deduped per job/deadline/UK day within the mounted tab session. Pause supported. No automatic permission prompt or notifications before opt-in. Tab closure stops reminders. |
| Spec/setup/context | UPDATED | Latest theme/reminder choices, exact setup limits, owner authorship preference and Google configuration retained. |

## Phase 1 acceptance

| Criterion | Result | Verification | Remaining limit |
|---|---|---|---|
| Ten pasted URLs create correct rows | PASSED — fixtures | 42-test API/service suite exercises ten URLs through queue/worker/extractor/DB; browser separately checks pasted fixture HTML through actual worker | Live vacancy pages not tested |
| Re-pasting creates no duplicates | PASSED — fixtures | Same suite checks stable IDs/count/history with tracking variants | Live source variations untested |
| Sheet import preserves all rows | NOT TESTED on development copy | Synthetic row/formula/notes/source-status preservation tests pass | Owner OAuth/copy setup missing |
| Status write touches only intended cell | NOT TESTED | Writes blocked in API, worker, service and client; blocking tests pass | Read-only import must pass, then separate owner approval required |
| Database/storage backup restores | PASSED — disposable data | Service integrity/checksum/tamper tests plus browser-requested backup and CLI restore verifying four jobs, reviewed fact and exact CV bytes | Owner laptop operational restore not tested |
| Sponsorship defaults UNVERIFIED | PASSED | API/DB/extraction tests and browser labels | No automatic evidence assessment enabled |

## Checks performed this session

- `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short` in apps/api: **42 passed**, one existing Starlette/httpx deprecation warning. No backend edits followed this run.
- `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build` in apps/web: **PASSED**, including final reminder component.
- `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen --group browser python ../../scripts/smoke_browser.py` in apps/api: **PASSED** with final theme/reminders and actual separate worker. Includes direct dashboard/reload/reopen/server restart, server-only token/origin guards, CRUD/history/profile/fact review, filters/sorting/counts, mobile navigation and 1440/390/320px layouts, CV and backup workflows above.
- Notification test replaces Notification API with a deterministic fake: verifies no automatic opt-in, correct due-job body and no duplicates after pause/re-enable. This does not prove native macOS notification display, denied-permission UI or long-running day rollover.
- Eleven dark foreground/background pairs pass >=4.5:1 contrast calculations. Charcoal desktop Dashboard screenshot visually inspected. Not a full accessibility audit.
- `git diff --check`: passed before delivery.

Initial browser extension failed at an exact label selector even though the CV candidate was rendered; corrected to role/name and reran the full suite successfully. An interrupted exploratory rerun left disposable processes; these were stopped before the successful final runs. Default uv cache was read-only, so checks used a /tmp cache. No safety controls were relaxed.

## Unfinished work and blockers

- Actual Google OAuth/read-only development-copy import is untested. No default OAuth client JSON exists in this cloud checkout. Owner must follow SETUP.md locally; never upload credentials in chat.
- Need development-copy spreadsheet ID, exact tab and header-row number. Headers are already supplied; do not ask again. Original Sheet remains blocked. No write approval exists.
- Native macOS notifications require browser/OS permissions and owner verification. Reminder permission/enablement is per tab session; reload requires Enable again. No service worker/background daemon or email delivery.
- PDF/DOCX have service tests; browser upload path tested with TXT only. Live URL evaluation/provider fallback and laptop operational restore remain unverified.
- No Phase 2, submissions, portal automation or hosted personal-data use authorised.

## Resume in this order

1. Read AGENTS.md and linked context/status/spec/setup; inspect Git state and latest remote SHA.
2. Help owner configure local OAuth using SETUP.md, then verify read-only import against their actual development copy. Never infer success from synthetic tests.
3. Verify macOS reminders and laptop backup/restore as owner setup permits.
4. Only after read-only import passes, seek separate approval before any Sheet write scope or implementation. Phase 2 still needs explicit owner confirmation.
5. Update status/handover, commit with owner-configured authorship, push checked scope and verify remote ref.

## Delivery and owner next step

Prepared files: stylesheet, reminder component, browser runner, README, spec/setup/status/context/handover. No dependencies, migrations, secrets or owner data included. Application commit `a625c01` was pushed and its full SHA matched the remote ref. This follow-up only records delivery; no runtime edits remain.

On Mac, stop the app with Control+C, then from the repository root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py
```

Open `http://127.0.0.1:3000`. Choose Enable desktop reminders on Dashboard and allow browser/macOS notifications. No dependency or migration update is required for this delivery.

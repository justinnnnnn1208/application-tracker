# Latest session handover

Reviewed: 9 November 2026 (Europe/London).

## Latest request and scope

The owner explicitly resumed the paused UI redesign after asking the agent to read AGENTS.md and the handover. The owner also asked to keep code and structure minimal. This delivery completes the existing Phase 1 UI changes and their styling/verification. Phase 2 remains paused until the owner confirms Phase 1 is verified.

Read [AGENTS.md](../AGENTS.md), [stable context](context/PROJECT.md), [SPEC.md](SPEC.md), [STATUS.md](../STATUS.md) and this file. [SETUP.md](SETUP.md) covers local startup and read-only Google setup.

## Work completed

- Resumed the three preserved UI edits rather than discarding/restarting them: `apps/web/src/app/layout.tsx`, `apps/web/src/components/tracker.tsx`, and `apps/web/src/components/workflows.tsx`.
- Replaced the old welcome/green styling with one light Inter/blue stylesheet (`apps/web/src/app/globals.css`), a 220px desktop sidebar, warm-grey workspace, white bordered cards and mobile top navigation.
- Dashboard now has compact URL intake, real last-Sheet-sync state, three required metrics, and the correctly filtered Closing soon table. Applied remains zero in this slice because confirmed submission is not implemented; imported source claims are not treated as confirmation.
- Jobs supports combined status/deadline/sponsorship filters, notes/location/company/role search, and deadline/newest/company sorting. Unknown deadlines sort last by deadline. Sponsorship is a text label with a neutral grey Unverified tag.
- Native details/summary controls collapse background tasks and settings. Removed duplicate form markup and an unnecessary setup-sidebar component from the earlier unfinished changes. No dependencies, backend code, database schema, services or new directory structure were added.
- The functional app label is Job Tracker. Later-phase matching/review queues are not advertised or enabled. Direct dashboard/server-only credential handling is preserved.

## Verification performed this session

| Check | Working directory | Result | Evidence/limit |
|---|---|---|---|
| `npm run typecheck` | `apps/web` | PASSED, exit 0 | Current component types |
| `NEXT_TELEMETRY_DISABLED=1 npm run build` | `apps/web` | PASSED, exit 0 | Final responsive CSS/components; build includes TypeScript checking |
| `uv run --frozen pytest -q --tb=short` | `apps/api` | PASSED, 42 tests, exit 0 | One dependency deprecation warning; no real portals, Google Sheet or hosted model called |
| `uv run --frozen --group browser python ../../scripts/smoke_browser.py` | `apps/api` | PASSED, exit 0 | Production servers with disposable DB/storage; direct dashboard/reload/reopen/server restart; origin/credential guards; manual jobs/history/profile/facts/deadlines; filters/search/sort; metrics; neutral sponsorship; native backup disclosure; all mobile nav items visible |
| Layout and touch checks inside browser smoke | Disposable production UI | PASSED | 1440px desktop, 390px all-page width checks, 320px Dashboard; tables scroll internally; enabled visible Dashboard controls have effective targets at least 44px |
| Palette contrast calculation | Repository root, inline Python | PASSED | 11 normal-size foreground/background palette pairs meet at least 4.5:1; not a full accessibility certification |
| Screenshot inspection | Ignored `.local/` artifacts | PASSED visual review | Dashboard desktop and narrow mobile, plus Jobs mobile; synthetic test rows only |

The smoke runner was updated for the new headings, filters and disclosures. An initial exact-text selector for the backup summary was corrected; the final complete run passed. A visually clipped mobile menu was changed to wrap, rebuilt and retested. No currently unresolved failure is being hidden by those fixes.

Snapshots remain ignored (`.local/dashboard-desktop.png`, `.local/dashboard-mobile.png`, `.local/browser-desktop.png`, `.local/browser-mobile.png`). They are not real owner data and are not committed. No original reference PNG is saved in the repository; the supplied chat references and written spec guided the styling.

## Phase 1 acceptance

| Criterion | Status | Evidence and remaining limit |
|---|---|---|
| Ten pasted URLs create correct job rows | PASSED — controlled fixtures | Current 42-test run exercises ten URLs through API/queue/worker/extractor/DB; no live vacancy set verified |
| Re-pasting creates no duplicates | PASSED — fixtures | Tracking-URL variants preserve IDs/count/history in the same current suite |
| Sheet import preserves every row | NOT TESTED on development copy | Synthetic preservation test passed; actual OAuth/copy import not configured/verified by this run |
| Status write touches only its target cell and preserves formulas/formatting/notes | NOT TESTED | All Sheet mutations remain disabled until read-only import is verified and the owner separately approves writes |
| Database/storage backup restores successfully | PASSED — disposable data | Current restore, file-byte, checksum, integrity and tamper tests; owner laptop restore not verified |
| Sponsorship defaults to UNVERIFIED | PASSED | Current API/DB/extraction defaults and non-inference tests; no automatic confirmed sponsorship implemented |

Phase 1 is still incomplete, with a rough progress indication of about 60%. The UI task being complete does not satisfy the outstanding integration criteria or authorise Phase 2.

## Remaining work and owner inputs

- Full browser workflows for CV upload/candidate confirmation, running backups, OAuth and read-only import are not yet verified. Existing service/fixture coverage is separate from those browser checks.
- Owner must configure OAuth locally using SETUP.md and provide the development-copy spreadsheet ID, exact tab and header-row number. Column names are already documented; do not ask for them again. Never request credentials or downloaded client JSON in chat.
- Extraction provider/model choice remains open before enabling hosted fallback. Personal data must not be sent to a hosted provider without the required approval.
- No writes to the original tracker, no enabling Sheet writes, no real portal run, no submission, and no Phase 2 start are authorised by this UI task.

## Next session

1. Read the entry-point/context/status/handover and inspect Git state. This UI redesign is complete; do not assume the old three-file WIP is still outstanding.
2. Follow the owner's next requested Phase 1 task. Good next verification work is the CV/backup browser flow or owner-configured development-copy import.
3. Keep services on localhost and tests on disposable data. Preserve `.env`, `.local/` and storage; never reset owner data to get an empty screenshot.
4. Update STATUS.md and this handover, push completed checked work to `dev/phase-1`, verify the remote ref, and give Mac pull/restart commands.

## Delivery

Branch: `dev/phase-1`. The checked UI/source was published in [`d20a19e`](https://github.com/justinnnnnn1208/application-tracker/commit/d20a19e0c135fbb74e11130d315368560b8c7d27); its full local SHA matched GitHub in a read-only remote-ref check. The worktree was clean after that application commit. This delivery-record follow-up changes documentation only. Context documentation previously landed in `e80d9c9` / `f1a7a40`; direct-dashboard support was previously delivered in `1c7c8e2`. No unfinished runtime edits remain from this UI task.

No owner configuration is required for this UI update. After delivery, stop the local app with Control+C, run `git pull --ff-only origin dev/phase-1` from the local project folder, and restart `python3 scripts/dev.py`. No dependency or migration refresh is needed for this change.

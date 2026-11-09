# Latest session handover

## Session

Reviewed: 9 November 2026 (Europe/London). Branch `dev/phase-1`; previous published baseline `7b15bf9`. Initial worktree clean.

Owner explicitly accepted deferring Phase 1 live write verification with Mac notification/operational restore checks outstanding and authorised Phase 2. Later clarified: prioritise real graduate/junior UK technology roles; sponsorship is informational and should not exclude jobs. No legal/right-to-work declaration changed. Owner is away for a run and asked independent work to continue. Sheets stays read-only by default; no automatic discovery schedule or portal/submission runs authorised.

## Completed work

| Work | State / evidence |
|---|---|
| Phase/selection preferences | Recorded in AGENTS/context/spec/status/setup; prior Phase 2 pause superseded by explicit owner approval. |
| Offline real-page evaluation harness | Implemented/tested: manifest paths/checksums/unique URLs/labels/quotes, field accuracy, failures in denominators and separate false-YES metric. No hosted/fetch calls. Empty genuine manifest deliberately not ready. |
| Public Greenhouse discovery | Implemented/tested with synthetic feed fixtures only. Fixed official API endpoint, validated slug, shared robots/host/rate/size guards, no redirects/bypass. Parses real-source fields without guessing missing dates/company or sponsorship. |
| API/worker/Settings | Existing dormant DiscoverySource table reused; add/list/delete source and manual queued task. Default disabled, real worker dedupes URLs and reports counts. Browser checks source add/remove and disabled import control. No dependencies/migrations added. |
| Cloud access proposal | Saved narrow two-domain draft, not applied. Startup guidance corrected to latest phase/selection decision. |

## Phase 1 acceptance / remaining deferrals

| Criterion | Result | Evidence and remaining limit |
|---|---|---|
| 10 pasted URLs correct | PASSED — fixtures | Real queue/worker/extractor/DB with mocked fetch; live 10-page set untested. |
| Re-paste dedupe | PASSED — fixtures | Canonical/tracking variants maintain IDs/count/history. |
| Preserve Sheet rows | PASSED — owner report + fixtures | Owner reports 20 rows and matching data; cloud has no private Mac connection. |
| Only intended status cell changes | NOT TESTED live — explicitly deferred | Exact RAW single-cell and safety/no-retry automated tests pass; live format/preservation comparison not performed. |
| Backup restore | PASSED — disposable data | Service and real-worker browser→CLI checks include exact CV bytes; operational Mac restore outstanding. |
| Default sponsorship UNVERIFIED | PASSED | API/DB/extraction/discovery fixture tests; no licence/Notes inference. |

Phase 1 accepted for progression with limitations, not marked 100% tested. Native Mac notification delivery also remains outstanding. Owner confirmed listing links/imported-status UI checks on Mac. Do not request those checks again without a new relevant change.

## Verification this session

- apps/api `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short`: **67 passed**, one existing dependency deprecation warning.
- apps/web `npm run typecheck`; `NEXT_TELEMETRY_DISABLED=1 npm run build`: **PASSED**.
- apps/api `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen --group browser python ../../scripts/smoke_browser.py`: **PASSED**, discovery source UI add/disabled-run/remove and prior production security/CRUD/filter/link/imported-status/CV/backup/reminder/responsive workflows. Test records are synthetic/disposable, never owner data.
- apps/api evaluation CLI with ../../fixtures/eval/manifest.json: **exit 2 expected**, empty dataset (NOT TESTED), not an accuracy/Phase 2 pass.
- Failed root-directory uv pytest attempts were corrected to apps/api; final full suite passed. No test failure was bypassed.

## Blockers and limits

Public Greenhouse robots probes were denied by enforced cloud proxy policy (403 tunnel denial). Runtime status: current observations true, restricted policy enforced, no custom permitted job hosts. Read cloud runtime skill/networking guide; no bypass attempted. Runtime skill applied: cloud-environment:cloud-environment-runtime.

Saved draft `cecfgdraft_ca60bddc6fc081998e5c4da96f887495` adds only boards-api.greenhouse.io and job-boards.greenhouse.io, and refreshes startup guidance. Existing install/repository/secret settings preserved. Tool confirmed saved, requires_publish true. Owner must review/save/publish in environment settings; draft save does not change running access. Refresh environment status and perform a fresh normal request after application before claiming readiness. No Google/portal credentials requested or added.

No real job pages saved: fixtures/eval/manifest.json remains empty. SPEC requires roughly 30 genuine hand-labelled postings before matching; no matching/scoring implementation was started. Numerical accuracy thresholds were proposed but the owner's reply clarified targeting rather than accepting numbers, so remain pending. Zero false CONFIRMED_YES is still mandatory, despite sponsorship being informational.

Discovery is the first manual Greenhouse slice only. It imports all records from the chosen board, not UK/junior-ranked results. Missing API company names use Employer not provided. Missing dates remain null. No automatic sources, schedules, fuzzy/cross-source merging, match scores, feedback, licensing signal, other ATS or aggregator support. Shared fetcher may reject large boards (>1 MB) or unavailable/disallowed robots. Live API behaviour remains unverified. Do not represent fixture jobs as actual vacancies.

## Resume in order

1. Read AGENTS.md and linked current context/spec/status/setup. Inspect Git state; preserve owner data and Git authorship.
2. Confirm the network draft was actually applied/published; refresh status and normal robots/API probes. If still denied, explain the precise missing host access rather than retrying/bypassing.
3. Respect terms/robots, save genuine public individual postings under fixtures/eval, retain source/capture/review/hash provenance and hand labels. Include diverse positive/negative/unknown cases; never seed fake jobs into the app.
4. Run baseline, review results and agree numeric thresholds. Only then build explainable matching, prioritising graduate/junior UK tech without sponsorship exclusion/penalty. No inferred legal declarations or hosted personal-data use.
5. Extend discovery as evidence warrants; test public-source transport/worker/UI. Keep Sheets read-only and original blocked.
6. Keep deferred Phase 1 checks in the record, update docs, commit/push checked work with owner's identity and verify remote SHA.

## Delivery

Code/tests/docs published as `ba9c99e64f4e75b308054c51e8d15cee1b7e8a7d`; local SHA matched GitHub dev/phase-1. This follow-up records delivery only; no unfinished runtime edits remain. Generated next-env.d.ts drift excluded. No owner configuration, credentials, storage, dependencies or migrations changed. Publication recorded in Git log and follow-up delivery note.

Mac update from project root after Control+C:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py
```

Settings → Job discovery shows new controls. No actual board is preconfigured. Configure only a source whose terms permit access; SETUP.md explains private URL_FETCH_ALLOWED_HOSTS and the separate cloud network draft. No Google permission update is needed. Matching is not available yet.

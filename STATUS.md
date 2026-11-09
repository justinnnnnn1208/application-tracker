# Current project status

Reviewed: 9 November 2026 (Europe/London).

**Phase 1: accepted for progression with explicit deferrals. Phase 2: authorised and started, roughly 10%.** Acceptance with deferrals does not mean every original Phase 1 check passed. The owner confirmed listing links/imported-status UI on the Mac, accepted live status-write verification as deferred, and retained native Mac notification/operational restore checks as outstanding.

## Current scope and implementation

The owner prioritises genuine graduate/junior UK technology postings. Sponsorship is informational, never an exclusion or score penalty. The owner mentioned the Graduate visa; no legal declaration, immigration eligibility or expiry was inferred or changed. Sheets remains read-only by default; no write setting or grant was enabled here.

- Existing local tracker, CV review, deadlines/reminders, backups and guarded default-disabled copy status writes remain available.
- New offline evaluation runner validates local saved-page paths, SHA-256, unique canonical URLs, labels and sponsorship quotes; reports field accuracy, extraction failures and false confirmed sponsorship separately. Failure cases remain in denominators. It does not fetch pages or call a model. The manifest is empty: **real benchmark NOT TESTED**, expected exit 2, not a pass.
- New Greenhouse adapter reads only the official public board API through existing allowlist/robots/rate/size guards. Settings supports adding/removing sources and requesting manual discovery. Worker imports valid published records, dedupes canonical URLs, reports invalid rows and leaves sponsorship UNVERIFIED. No seeded boards, automatic runs, form interaction, legal/profile use or hosted processing.
- First discovery version imports the chosen board, without UK/junior ranking. Missing company metadata uses an explicit unknown label; missing dates stay null. Live API behaviour unverified. Cross-source fuzzy merging, matching/scoring, feedback, licensing data, other ATS/aggregators are not implemented.

## Phase 1 acceptance record

| Criterion | Result | Evidence / limit |
|---|---|---|
| 10 URLs create correct rows | PASSED — controlled fixtures | API→queue→worker→extractor→DB tests; ten live vacancy pages not tested. |
| Re-pasting avoids duplicates | PASSED — fixtures | Canonical/tracking URL variants preserve IDs/count/history. |
| Sheet preserves all rows | PASSED — owner report + fixtures | Owner reports 20 jobs and matching data; synthetic tests cover incomplete rows/formulas/Notes/source statuses. No independent access to Mac OAuth session. |
| Status changes only intended cell | NOT TESTED live — explicitly deferred | Exact one-cell RAW HTTP/worker tests, formula/move/concurrent/duplicate/Notes guards and no-retry tests pass; live formatting preservation check outstanding. |
| Backup restores | PASSED — disposable data | Checksums/integrity/tamper and real-worker UI backup→CLI restore verify DB/facts/CV bytes. Operational Mac restore outstanding. |
| Sponsorship defaults UNVERIFIED | PASSED | API/DB/extraction/discovery fixture tests; no automatic inference from licences or Notes. |

## Current checks

- apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short`: **67 passed**, one existing Starlette/httpx deprecation warning.
- apps/web: `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build`: **PASSED**.
- apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen --group browser python ../../scripts/smoke_browser.py`: **PASSED**, including Settings discovery source creation, disabled-source control and removal. Existing direct-dashboard/security/CRUD/filters/imported Applied/link/CV/backup/reminder/responsive checks also pass. No real discovery or Google call during tests.
- Evaluation CLI on empty real manifest: **exit 2 as intended**, zero pages, dataset_ready false, phase_2_accepted false. Runner tests use synthetic fixtures only and must never be reported as real postings.
- No extraction/scoring/sponsorship algorithm changed by this slice. Real evaluation baseline remains blocked, not waived. Matching must wait for the roughly 30 real reviewed postings required by SPEC.md. Numeric accuracy thresholds remain unagreed; zero false CONFIRMED_YES stays required.

## Network blocker and saved draft

Default sandbox requests to Greenhouse robots.txt returned `URLError: Tunnel connection failed: 403 Forbidden`. Environment status confirmed current enforced restricted policy has no custom job-source hosts. No bypass/alternate transport was attempted.

Saved environment draft `cecfgdraft_ca60bddc6fc081998e5c4da96f887495` adds only `boards-api.greenhouse.io` and `job-boards.greenhouse.io`, preserves install/repository/secret settings and updates obsolete startup phase guidance. Save returned status saved and requires_publish true. **It is not applied or published.** Owner must review/save/publish in environment settings; then recheck observed policy and a fresh permitted request. See SETUP.md. No credentials needed for these public endpoints.

Next: apply permitted network settings, collect and hand-label genuine diverse public vacancies, agree thresholds, then build matching. Real portal forms/submissions and hosted personal-data use remain unauthorised. Keep Phase 1 deferrals recorded. Current code/tests/docs are prepared for owner-authored commit/push; delivery is recorded in HANDOVER.md and Git log.

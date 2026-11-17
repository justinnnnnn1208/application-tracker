# Latest session handover

## Session

Reviewed: 17 November 2026 (Europe/London). Branch dev/phase-1, previous published baseline a330be9. Initial worktree clean. User asked to continue Phase 2, then prioritised fixing role titles/descriptions because all summaries are already in Sheet column E (Notes). They asked for existing jobs to be updated, then went to bed and allowed continuation tomorrow if needed. Standing instruction: push completed tested work and update phase status.

Phase 2 roughly 50%, incomplete. Phase 1 accepted for progression with live write test deferred and Mac notification/operational restore checks outstanding. Sheets stays read-only; original tracker remains blocked. No Google OAuth connection or private Mac DB is accessible from this cloud workspace. Do not claim Mac rows were directly changed here. Pull/restart applies the local startup repair automatically; no re-entry of the 20 rows or new Google permission is needed.

## Changes completed

- Added literal Notes role/location parsing and idempotent API startup repair of Sheet-linked jobs. It uses already-imported Job.notes, not live Google/network access. Clear first-sentence role text and explicit supported UK place names fill missing fields; company-only/opportunity entries stay unknown. Compare-and-swap protects concurrent owner edits.
- Import/re-import fills missing details and refreshes only previously Notes-derived fields. Ownership markers use existing SheetLink.last_db_values JSON, no migration. Manual/official-source replacements are protected; later official listing extraction can replace still-auto-derived details. Notes/raw snapshots/formulas, IDs, company, dates and application/history statuses are preserved.
- UI uses “Description from Notes” when full vacancy text is absent, without duplicating the same Notes section. Matching accepts a real role plus a Notes summary with an explicit limited-source notice. Notes changes invalidate stored scores (preference-v2).
- Added batch Score active jobs, current-score column and highest-match sort in Jobs. API summaries hide stale/inactive/incomplete scores; actual current zero remains a real score. Batch snapshots up to 500 ready active jobs, excludes imported Applied/closed/past dates, rechecks at worker execution, reuses unchanged caches and deduplicates identical queued batches. No submissions/status changes/Sheet writes.
- Shared matching context avoids repeatedly loading profile/facts for every batch/list row. Existing scores/explanations and individual feedback remain supported; no automatic weight tuning.
- No dependencies, new tables, migrations, credentials, private settings, owner storage or environment configuration changed here.

## Phase 1 acceptance record

| Criterion | Result | Evidence/remaining limit |
|---|---|---|
| 10 URL rows correct | PASSED — fixtures | Current real API/worker/extractor suite; live ten-URL acceptance not claimed. |
| Re-paste dedupe | PASSED | Fixtures and earlier live Monzo repeat (60 jobs, zero added on repeat). Cross-source merge not implemented. |
| All Sheet rows preserved | PASSED — owner report + fixtures | Owner previously confirmed 20/data/UI; current tests preserve 20 Notes rows and repeat import without writes/duplicates. Actual Mac backfill still needs pull/restart. |
| Intended-cell-only write | NOT TESTED live — explicitly deferred | Existing guardrail tests pass; no write access enabled or Google cells edited. |
| DB/storage restore | PASSED — disposable data | Current service/browser/CLI checks include exact CV bytes; Mac operational restore outstanding. |
| UNVERIFIED default | PASSED | Current API/DB/extraction/discovery/import tests. Notes sponsorship claims do not affect confirmation or scores. |

Native Mac notification delivery also outstanding. Keep accepted deferrals recorded, not marked passed.

## Verification this session

- apps/api: UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short: **96 passed**, one existing Starlette/httpx deprecation warning.
- apps/web: npm run typecheck and NEXT_TELEMETRY_DISABLED=1 npm run build: **PASSED** with final rank/summary UI.
- Production browser smoke: **PASSED** on final application code. Simulates an old import, restarts the API, verifies automatic role/location repair and single visible Notes summary/limited-source notice; then scores a batch and checks highest-match sort. Existing security/CRUD/status/filter/link/imported Applied/CV/backup/discovery/reminder/responsive flows also pass. Uses disposable data and actual worker, no Google calls or owner data.
- Notes fixture uses the 20 supplied public summaries with synthetic company names/URLs: 19 clear roles, company-only row stays unknown. Startup repair/restart idempotence, owner-field protection, Notes refresh, official-source enrichment and preserved historical statuses tested. This is not a claim the Mac DB has already been changed.
- Batch tests cover current-score reuse, queued batch dedupe, missing/closed/applied/past exclusions, worker status recheck and stale/inactive numeric score hiding.
- Real 30-page evaluation rerun with --role-classification: exit 0, 30 pages, zero extraction failures/false YES, unchanged development metrics. Four employers/one ATS, no held-out generalisation or exact start-date positives; sponsorship remains unverified/abstaining.
- git diff --check passed before staging; generated next-env.d.ts drift excluded. Public-page fixtures/reports unchanged.

An initial new test referenced an expired ORM object after closing its session; corrected the fixture ID capture. First extended browser run needed apps/api on Python's module path for its DB fixture; corrected and reran successfully. No application check or safety guard was bypassed.

## Remaining scope and next session

Continue Phase 2: cross-source identity/aliases and conservative fuzzy dedupe, more ATS/aggregator support, weight-editing/feedback tuning, evidence review/licence signal, held-out/multi-ATS and exact-start-date validation. Current scoring is a local finite-keyword heuristic, not an LLM requirement extractor or personal/legal eligibility. No automatic discovery schedule, hosted personal-data processing, forms/submissions or Sheets writes authorised.

Numerical initial targets already agreed: >=90% deadline/location/graduate-role/start-date accuracy and zero false YES; report unknown-label coverage separately. Do not ask for those targets, supplied headers/copy IDs or the 20 rows again. Network grants are already published/working; do not reapply or publish environment settings without a new request. App-level host opt-in is separate (SETUP.md).

Read AGENTS/context/spec/status/setup, inspect Git and preserve owner data/authorship. Check the actual environment rather than assuming processes/OAuth readiness. The user should see Notes-based titles/summaries after pulling/restarting; if not, diagnose locally with redacted app errors, never ask for secrets/client JSON/callback URLs.

## Delivery / owner next step

Notes repair/ranking code and docs prepared for owner-authored commit/push; publication recorded in follow-up/Git log. No uncommitted runtime work deliberately excluded except generated next-env.d.ts drift (restored).

After Control+C, from the Mac project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py
```

Startup repairs existing imported data automatically. No new migration/dependency/permission/re-import required for already stored Notes. Newer edits in Google after last import still need Import test copy. Jobs → Score active jobs → wait in Background tasks → Preference match (highest). One company-only entry may still need an actual role, but its full Notes summary is visible. Google account/original Sheet remain untouched by this delivery.

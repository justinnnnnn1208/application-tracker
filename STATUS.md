# Current project status

Reviewed: 17 November 2026 (Europe/London).

**Phase 2: in progress, roughly 60%.** Phase 1 was accepted for progression with explicit deferrals; its untested checks are not marked passed. Sheets remains read-only by default. Discovery/matching prioritises graduate/junior UK tech roles, with sponsorship informational and excluded from scores. No immigration eligibility or legal declarations changed.

## Current delivery

- Published environment network grants verified as current/enforced, then both robots files returned 200 and allowed the source paths. No environment configuration was reapplied or published this session.
- Saved 30 genuine posting excerpts from four employers on Greenhouse, with independently reviewed labels, source/capture/review dates, excerpt hashes and original-response hashes. Forms/scripts/tracking markup excluded; no generated job metadata added. Raw responses remain ignored locally. See fixtures/eval/LABEL_REVIEW.md and provenance.json.
- Added Greenhouse visible-header/description extraction because live pages did not expose JobPosting JSON-LD. Validates source URL and consistent employer/title metadata; handles repeated headings and markup whitespace. Explicit full labelled dates are extracted; missing day/year remains unknown. Discovery reuses these date rules.
- Added narrowly scoped proxy DNS fallback for the two fixed official HTTPS hosts when local DNS is unavailable and an HTTPS proxy is configured. Other hosts, private DNS results, nonstandard ports and insecure HTTP remain blocked. Existing TLS/robots/allowlist/rate/size guards retained (docs/decisions/proxy-dns.md).
- Local per-job preference matching now runs in the worker: six explained criteria, reviewed fact citations, no sponsorship weight, current-score feedback and hash-based stale detection. It is a heuristic, not eligibility or a success probability. Feedback is stored but does not auto-tune weights.
- The owner clarified column E Notes contains role/description summaries. Existing Sheet-linked jobs now auto-backfill missing literal role/location fields at API startup; Notes render as a labelled description fallback. In a fixture based on all 20 supplied summaries, 19 roles are identifiable; the company-only entry stays unknown. This code has not directly changed the private Mac database; pulling/restarting applies the local repair.
- Notes-derived field ownership is kept in existing SheetLink JSON so repeat import refreshes generated fields but protects manual/official-source replacements. Matching supports summary-only input with an explicit notice. Notes changes invalidate scores.
- Jobs now supports batch active-job scoring and highest-current-score sorting. Pending identical batches dedupe, current scores are reused, and closed/past-deadline/incomplete jobs are excluded. Old/stale/inactive values are hidden from numeric ranking. No schema/dependency changes.

## Phase 1 acceptance record

| Criterion | Result | Evidence / limit |
|---|---|---|
| Ten URLs create correct rows | PASSED — fixtures | Current API/worker/extractor tests; no claim of a live ten-URL acceptance run. |
| Re-pasting avoids duplicates | PASSED | Fixtures; live Monzo worker import/re-import also preserved 60 jobs. Cross-source fuzzy dedupe remains unfinished. |
| Sheet preserves all rows | PASSED — owner report + fixtures | Owner confirmed 20 rows/data and UI checks on Mac; no independent cloud access to private OAuth session. |
| Only intended status cell changes | NOT TESTED live — explicitly deferred | Existing single-cell/guardrail tests pass. No write access enabled. |
| Backup restores | PASSED — disposable data | Service and browser/CLI restore check DB/facts/CV bytes. Mac operational restore outstanding. |
| Defaults UNVERIFIED | PASSED | API/DB/extraction/discovery checks; source Notes/licences do not become confirmations. |

Native Mac notification delivery is also outstanding. These accepted deferrals do not block the authorised Phase 2 work.

## Current verification

- API suite: **113 passed** (one existing Starlette/httpx deprecation warning), `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short` in apps/api.
- Frontend: `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build` passed.
- Latest production browser smoke passed with a real disposable worker: simulated old Sheet import → API restart → automatic title/location repair, visible single Notes summary and summary-only warning, batch scoring/highest-score sort, plus existing match explanation/feedback, security/CRUD/filter/link/imported-status/CV/backup/reminder/discovery/responsive checks.
- Earlier live check (not repeated for this local Notes update): normal application fetcher successfully fetched/extracted a Graphcore graduate vacancy (Bristol, deadline 29 November 2026).
- Earlier disposable live API→queue→worker imported 60 Monzo postings, then re-imported: 0 added, 60 duplicates, 0 invalid rows, still 60 stored jobs. All remained DISCOVERED/UNVERIFIED. Temporary data removed; no owner DB/Sheet or portal form interaction.
- Checked extraction and role reports committed under fixtures/eval/reports. All 30 development cases extract; company/title/location/deadline/start-date labels match 30/30; role classification matches 30/30. Twelve known deadlines match. All 30 start dates are null (no exact-day positive coverage). No held-out data or second ATS represented.
- Sponsorship remains unverified: 0 YES predictions, 0 false YES, 4 labelled positives and 14 labelled negatives. Forty-percent sponsorship label accuracy reflects abstention, not a finished evidence classifier. Phase 2 accepted remains false in reports.
- Owner agreed initial >=90% targets for deadline/location/graduate-role/start-date labels and zero false confirmed YES. Development targets meet the numeric aggregate; start-date positive coverage and generalisation remain unverified.

## Remaining Phase 2 work

Cross-source/fuzzy dedupe and aliases; more sources/ATS; manual weight controls/tuning from feedback; evidence review and licensed-sponsor signal; held-out and multi-ATS evaluation including exact start dates. LLM structured requirement extraction has not been introduced; current matching is a transparent local heuristic with a finite technology vocabulary. No automatic discovery scheduling added. Phase 2 is not complete.

On Mac: pull/restart, allow the approved public source host(s) in private URL_FETCH_ALLOWED_HOSTS per SETUP.md, and use Settings → Job discovery or paste a supported listing URL. Open job details → Calculate preference match. Already-imported Notes repair locally on restart; company-only rows still need a real role. Notes summaries are explicitly marked when used for scoring. No new dependencies or migrations. No credentials or personal facts were sent to hosted models.

Previous published baseline was a330be9. The checked Notes repair/ranked-list delivery was pushed with owner-configured authorship as dc6f0f3; its full local SHA matched GitHub dev/phase-1. The documentation-only follow-up records delivery; no unfinished runtime edits remain. No owner configuration/data, Google cells or environment settings were changed from this cloud workspace.

## Night-shift checkpoint — 19 November 2026, step 1

Source identity/alias intake, traceable source UI and conservative fuzzy-review hints are implemented. New migration 7419a825bc10 creates/backfills source records without combining old jobs or rewriting histories. Known posting identifiers across official URL variants retain one job/application; ambiguous existing identities reject intake. The Sheet row guard compares the actual row alias URL, so approved copy status checks remain one-cell only (writes still disabled by default).

Migration helper `python3 scripts/dev.py --migrate` loads private settings, refuses a running worker, backs up/restores-verifies existing SQLite data and applies the correct configured DB migration before launching. Memory/URI/non-SQLite DBs are rejected by this helper. Behind-schema API startup fails with the update instruction. Migration round-trip/no-drift, legacy data/history, backup bytes/custom DB and worker-lock tests pass.

Step 1 API suite: 113 passed; build/typecheck passed; source-alias browser flow passed, final helper/head-check browser run passed. Next step is owner-controlled matching weights/feedback controls. No real Google write, portal form, personal hosted processing or environment publication performed.

# Current project status

Reviewed: 17 November 2026 (Europe/London).

**Phase 2: in progress, roughly 40%.** Phase 1 was accepted for progression with explicit deferrals; its untested checks are not marked passed. Sheets remains read-only by default. Discovery/matching prioritises graduate/junior UK tech roles, with sponsorship informational and excluded from scores. No immigration eligibility or legal declarations changed.

## Current delivery

- Published environment network grants verified as current/enforced, then both robots files returned 200 and allowed the source paths. No environment configuration was reapplied or published this session.
- Saved 30 genuine posting excerpts from four employers on Greenhouse, with independently reviewed labels, source/capture/review dates, excerpt hashes and original-response hashes. Forms/scripts/tracking markup excluded; no generated job metadata added. Raw responses remain ignored locally. See fixtures/eval/LABEL_REVIEW.md and provenance.json.
- Added Greenhouse visible-header/description extraction because live pages did not expose JobPosting JSON-LD. Validates source URL and consistent employer/title metadata; handles repeated headings and markup whitespace. Explicit full labelled dates are extracted; missing day/year remains unknown. Discovery reuses these date rules.
- Added narrowly scoped proxy DNS fallback for the two fixed official HTTPS hosts when local DNS is unavailable and an HTTPS proxy is configured. Other hosts, private DNS results, nonstandard ports and insecure HTTP remain blocked. Existing TLS/robots/allowlist/rate/size guards retained (docs/decisions/proxy-dns.md).
- Local per-job preference matching now runs in the worker: six explained criteria, reviewed fact citations, no sponsorship weight, current-score feedback and hash-based stale detection. It is a heuristic, not eligibility or a success probability. Feedback is stored but does not auto-tune weights.
- Imported stubs require actual role/vacancy details before scoring. Re-pasting a supported URL can fill missing fields while preserving Notes, statuses/history, identity and existing owner content. No duplicate job is created.

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

- API suite: **84 passed** (one existing Starlette/httpx deprecation warning), `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short` in apps/api.
- Frontend: `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 npm run build` passed.
- Production browser smoke passed with real disposable worker: matching score, explanation and feedback, plus existing security/CRUD/filter/link/imported-status/CV/backup/reminder/discovery/responsive checks. Final discovery date-parser adjustment has API/service coverage; browser matching/UI code was unchanged by it.
- Normal application fetcher successfully fetched/extracted a live Graphcore graduate vacancy (Bristol, deadline 29 November 2026).
- Disposable live API→queue→worker imported 60 Monzo postings, then re-imported: 0 added, 60 duplicates, 0 invalid rows, still 60 stored jobs. All remained DISCOVERED/UNVERIFIED. Temporary data removed; no owner DB/Sheet or portal form interaction.
- Checked extraction and role reports committed under fixtures/eval/reports. All 30 development cases extract; company/title/location/deadline/start-date labels match 30/30; role classification matches 30/30. Twelve known deadlines match. All 30 start dates are null (no exact-day positive coverage). No held-out data or second ATS represented.
- Sponsorship remains unverified: 0 YES predictions, 0 false YES, 4 labelled positives and 14 labelled negatives. Forty-percent sponsorship label accuracy reflects abstention, not a finished evidence classifier. Phase 2 accepted remains false in reports.
- Owner agreed initial >=90% targets for deadline/location/graduate-role/start-date labels and zero false confirmed YES. Development targets meet the numeric aggregate; start-date positive coverage and generalisation remain unverified.

## Remaining Phase 2 work

Cross-source/fuzzy dedupe and aliases; more sources/ATS; global ranked job list; manual weight controls/tuning from feedback; evidence review and licensed-sponsor signal; held-out and multi-ATS evaluation including exact start dates. LLM structured requirement extraction has not been introduced; current matching is a transparent local heuristic with a finite technology vocabulary. No automatic discovery scheduling added. Phase 2 is not complete.

On Mac: pull/restart, allow the approved public source host(s) in private URL_FETCH_ALLOWED_HOSTS per SETUP.md, and use Settings → Job discovery or paste a supported listing URL. Open job details → Calculate preference match. Missing Sheet descriptions must be filled/enriched first. No new dependencies or migrations. No credentials or personal facts were sent to hosted models.

Code/tests/docs prepared for owner-authored commit/push; HANDOVER.md and Git log record final publication.

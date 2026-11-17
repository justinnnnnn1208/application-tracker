# Latest session handover

## Session

Reviewed: 17 November 2026 (Europe/London). Branch dev/phase-1; previous published baseline 5e2e4af. Initial worktree clean. User resumed after publishing the environment and explicitly forbade reapplying/publishing settings; this instruction was respected. They reiterated pushing finished work and updating phase status.

Phase 2 is authorised. Owner agreed initial >=90% field accuracy (deadline/location/graduate-role/start date), with zero false sponsorship confirmations. Prioritise real graduate/junior UK tech; sponsorship is informational, not an exclusion/score penalty. No legal declarations changed. Phase 1 live Sheet write test deferred by owner; native Mac notification/operational restore checks remain outstanding. Sheets stays read-only.

## What changed

- Confirmed applied/enforced Greenhouse network grants and fresh accessible robots/API/page responses. No configuration update or publication.
- Collected and reviewed 30 genuine postings from Graphcore (14), Canonical (8), Monzo (4), Deliveroo (4). Excerpts retain original job metadata/logo/header/description; forms/scripts/tracking removed, no fabricated JSON-LD. Sources, dates, excerpt and raw hashes in manifest/provenance; raw HTML remains ignored. LABEL_REVIEW.md explains graduate/date/sponsorship decisions. Four employers/one ATS: development set, not held-out quality proof.
- Added visible Greenhouse parser for live pages lacking JSON-LD. Consistent page URL/title/employer required; handles placeholder page titles using original logo + matching og:title, whitespace and identical repeated h1. Scripts/forms ignored. Full labelled dates parsed; incomplete dates remain null. Discovery reuses explicit date parsing.
- Local DNS failed while proxy HTTPS worked. Added fallback only for the two fixed official HTTPS hosts with configured proxy, only on DNS OSError, never private/non-global results. Other URL/TLS/robots/rate/size guards retained. Decision docs explain rationale/tests.
- Implemented local worker preference score, explained criteria/fact IDs, API/current-score feedback/stale detection and job-detail card. Six weights total 100, sponsorship absent. Reviewed facts only; no name/email/declarations used. Rating does not auto-tune weights.
- Added missing-source-data guard: no score for imported stubs without title/vacancy text. Re-pasted supported URLs and discovery can fill only missing fields; preserve populated owner fields, Notes/tracker/app status/history and job ID.
- Updated evaluation runner for optional role-classification mode, known-label counts/accuracy and positive sponsorship prediction/label counts to expose abstention. Reports explicitly do not accept Phase 2.

## Phase 1 checklist

| Criterion | Result | Evidence / limits |
|---|---|---|
| 10 URL rows correct | PASSED — fixtures | Current API→worker→extractor; live ten-URL acceptance not claimed. |
| Re-paste dedupe | PASSED | Fixtures and live disposable Monzo repeat: 60 jobs, 0 duplicates added. Cross-source fuzzy merge not implemented. |
| All Sheet rows preserved | PASSED — owner report + fixtures | Owner confirmed 20/data/UI; no private Mac OAuth access here. |
| Intended-cell-only write | NOT TESTED live — deferred | Existing guardrail tests pass; no write enabled. |
| DB/storage restore | PASSED — disposable | Current service/browser/CLI checks; operational Mac restore outstanding. |
| UNVERIFIED default | PASSED | Current API/DB/extraction/discovery tests, no automatic YES. |

Native Mac notifications also outstanding. These are accepted progression deferrals, not passed laptop checks.

## Verification

- apps/api: UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short: **84 passed**, one existing deprecation warning.
- apps/web: npm run typecheck; NEXT_TELEMETRY_DISABLED=1 npm run build: **PASSED**.
- Production browser smoke: **PASSED** with final matching UI (real worker score/explanation/feedback) and existing security/CRUD/filter/link/imported-status/CV/backup/discovery/reminder/mobile checks. Discovery's final explicit-date parser adjustment is service/API-tested; no subsequent UI edits.
- Live normal-app fetcher: Graphcore Graduate Software Engineer, DevOps 2027, Bristol, explicit 2026-11-29 deadline extracted. No form interaction.
- Disposable live API/worker Monzo board import: first 60 read/60 added/0 invalid; second 60 read/0 added/60 duplicates/0 invalid; 60 stored jobs all DISCOVERED/UNVERIFIED. Temporary DB/storage removed, owner data untouched.
- Offline extraction baseline and --role-classification report commands: **exit 0**, 30 cases, 0 extraction failures, basic fields 30/30, role mode graduate 30/30. Known deadlines 12/12. Start-date positives 0; all 30 null. Sponsorship 0 YES predictions, 0 false YES, 4 positive labels, 14 negative, 12 unknown; no finished evidence assessment.
- Reports/labels reflect development using these cases, not independent held-out performance. Full Phase 2 accepted=false.

An initial live app fetch was blocked by unavailable local DNS, despite successful normal proxied HTTP. The narrow fallback fixed the actual client, not environment permissions; no DNS/TLS/proxy bypass. Earlier root-directory uv test attempts were corrected to apps/api and final full checks passed. No test failure was hidden. Generated next-env.d.ts drift excluded.

## Remaining / next actions

Phase 2 roughly 40%, incomplete. Next useful work: cross-source identity/aliases and conservative fuzzy dedupe; ranked jobs view using current matches; source enrichment support beyond Greenhouse; manual weight editing/tuning feedback; evidence review/licence signal; held-out multi-ATS and exact-start-date examples. Current finite-keyword preference scoring is not LLM requirement extraction or personal eligibility. Do not infer sponsorship need from visa policy or send personal facts to hosted models.

API matching routes: POST /tasks/match {job_id}, GET /jobs/{id}/match, POST /jobs/{id}/feedback {value: good|bad}. The worker uses only reviewed facts and fingerprints job/fact/preference inputs. Old scores become stale; current feedback only. Recalculating unchanged inputs preserves feedback. Matching insufficient imported rows returns 409; UI explains enrichment.

Network configuration is published and working on the current environment; do not ask user to publish the previous draft again. Do not modify or publish environment settings unless newly requested. App-level URL_FETCH_ALLOWED_HOSTS remains a separate opt-in; test commands used per-process approved hosts, never changed private .env. Original tracker blocked and Sheets readonly.

## Delivery / resume

Prepared for owner-authored commit/push; publication recorded in follow-up and Git log. No dependencies/migrations, owner credentials/configuration/storage or legal facts changed. Public posting data only is added to tracked fixtures; raw application-form HTML stays ignored.

Read AGENTS/context/spec/status/setup, inspect Git and use latest confirmed state. Never assume an app process, published setting or private OAuth session is available from this handover alone.

Mac after Control+C, from project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py
```

No dependency/migration refresh needed. For discovery/URL fetching, merge boards-api.greenhouse.io and job-boards.greenhouse.io into the private approved host list as documented in SETUP.md, review source terms, and restart. Choose a source manually. Job details now show Calculate preference match and Why this score. Import stubs need a real title/description first; re-pasting a supported URL fills missing details without overwriting owner history. Google permission need not change.

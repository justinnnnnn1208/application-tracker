# Current project status

Reviewed: 20 November 2026 (Europe/London).

**Phase 2: roughly 90% implementation; acceptance incomplete.** Percentages are estimates, not quality certificates. Phase 1 was accepted for progression with explicit operational deferrals. Sheets stays read-only by default. Phase 3, submissions and environment publication are not authorised.

## Implemented and checked

| Capability | Current behaviour and evidence |
|---|---|
| Local tracker | Direct charcoal dashboard, jobs/deadlines/listing links, imported statuses, profile/CV fact review, worker and opt-in tab-open reminders. Owner confirmed 20 development-copy rows. Notes locally repair missing literal role/location fields; owner edits/history/raw Sheet values are preserved. |
| Identity and dedupe | Canonical URLs and official provider/board/posting identities retain one application and traceable aliases. Global/EU namespaces are separate. Fuzzy matches are review hints; conflicting existing histories are not automatically merged or split. Fixture tests and fresh live saved-page → API → repeat preservation pass. |
| Preference matching | Six deterministic explained criteria, reviewed-fact citations, active-job batch scoring, current/stale ranking, Good/Poor feedback and manual keyword/weight controls. Sponsorship/immigration terms do not penalise scores. This is not personal/legal eligibility, proficiency or success probability. |
| Public discovery | Greenhouse, Lever global/EU, Ashby and SmartRecruiters; Reed keyword search with private API key. SmartRecruiters/Reed cover the first 20 results with detailed text. Greenhouse live checks pass; other providers have synthetic contract/worker/browser coverage, with live compatibility unverified. No schedule or seeded sources. Repeated pending source requests reuse a task. |
| Local requirement candidates | Explicit per-job Ollama tasks, source quotes/schema validation, bounded input/output/retries and stale/concurrent-source protection. No Notes/profile/facts/CV/legal inputs. Current technology candidates feed deterministic overlap; otherwise labelled finite-keyword fallback. Both Ollama paths enforce loopback endpoints and ignore shell proxies/redirects. Synthetic HTTP tests are not real model quality. |
| Sponsorship review | Owner-confirmed source quote and saved listing URL, context fingerprint, stale/legacy rejection and clear action. Provenance checks do not establish the statement's meaning. Automatic role-policy assessment is not delivered; default remains Unverified. |
| Licence signal | Dated owner-confirmed official-asset CSV upload, conservative exact organisation-name lookup, separate route/town/source/hash display. Full parsing precedes atomic cache replacement; snapshots are retained/backed up. This is not online provenance verification, legal-employer identity or role sponsorship. |
| Safe updates/backups | Backup-verifying `python3 scripts/dev.py --migrate`, schema guard and non-destructive CLI restore. Migration head eb81a592c387; cached identity migrations preserve existing jobs/history. Restore now rejects incomplete/unsupported/duplicate-member archives; URI-safe read-only snapshots honour database paths containing #, literal percent escapes or spaces. No new dependencies; private configuration/encryption keys remain unchanged. |

## Phase 1 acceptance record

| Criterion from SPEC | Result | Verification / remaining limit |
|---|---|---|
| Ten pasted URLs create correct rows | PASSED — controlled fixtures | API → queue → worker → extractor. Ten live sites are not claimed. |
| Re-pasting creates no duplicates | PASSED | Fixtures, earlier live Monzo 60 → zero new/60 duplicates, fresh MW 4 new/1 duplicate then zero new/5 duplicates. Seeded shortlist/two events preserved. |
| Sheet import preserves all rows | PASSED — owner + fixtures | Owner confirmed all 20 development-copy rows/data/UI. Tests preserve Notes/formulas/history. Cloud cannot inspect the private Mac OAuth session. |
| Only intended status cell changes | NOT TESTED live — explicitly deferred | Single-cell/alias-row/guard fixtures pass; no live cells edited or write access enabled this run. |
| Database/storage backup restores | PASSED — disposable data | Service/browser/CLI verify DB/facts/CV/register bytes and migration backups. Mac operational restore remains untested. |
| Every job defaults Unverified | PASSED | API/database/import/extraction/discovery plus owner-review, source-bound/stale/clear guards. Licence/model/source wording cannot self-confirm. |

Native macOS notification delivery remains untested. These accepted deferrals are not passed operational checks.

## Latest verification

- **303 API tests passed**, one existing Starlette/httpx deprecation warning. From apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short`.
- Latest frontend typecheck and production build passed on the SmartRecruiters UI; subsequent changes are backend/data/docs only.
- Production browser passed: disposable real worker, direct dashboard/reload/restart, server-only credential/origin guards, CRUD/history, Notes repair, CV review/download, filters/deadlines, preferences/feedback/evidence, source controls, synthetic native Ollama task, register upload, backup/CLI restore, notification mocks and 1440/390/320px layouts.
- Fresh live strict-ID Greenhouse import passed in temporary storage: 4 new + 1 duplicate, repeat 0 new + 5 duplicates; one application each, saved shortlist/history preserved, all Unverified. No applicant facts/model/Google/forms. Reports/capture hashes distinguish live evidence from fixtures.
- Greenhouse malformed/conflicting board/ID/URL tests reproduced failures before hardening. They now skip invalid entries, preserve publisher custom links without trusting arbitrary query IDs, and allow literal EU listing scope returned by the shared API. One additional malformed-content test initially failed; explicit type validation fixed it, then the full suite passed.
- Local proxy regression reproduced failure before the direct-client fix and passed after. Backup review reproduced missing-DB/unsupported-manifest acceptance and URI-filename mistakes; strict format checks and URI-safe paths now pass targeted/full/browser checks. One percent-filename test first encoded a different SQLAlchemy path, was corrected to a rendered URL, and proves both app-driver and restored-row identity. No unresolved application-test failure at this checkpoint.

## Real-page and model evaluation

Original 30 and 19 November 35 manifests stay frozen. `fixtures/eval/manifest-nov20.json` contains **38 genuine excerpts across six employer labels, all Greenhouse**. Three new GoCardless labels were frozen before initial prediction: Junior Data Analyst in Riga, Data Science Manager and Senior SRE in London. Initial fields/role controls matched; the 3-case-only probe exits 2 because it is below the 30-page dataset-readiness minimum. The combined regression exits 0. Future runs are regressions after label inspection.

Current field/role regression matches labels with zero extraction failures/false YES. Known coverage: 12 deadlines, 3 exact start dates, 32 role-level YES/NO labels. The three date positives share one Marshall Wace template; the new null-date controls do not improve positive-date coverage. The original Nov19 0/3 held-out date failure remains saved. Automatic sponsorship abstains (4 YES/14 NO labels; zero known-policy accuracy). Zero false YES from abstention does not measure evidence-assessment quality. **phase_2_accepted remains false.** See fixture review/provenance files.

`python3 scripts/dev.py --check-model` runs the local-model check from the project root, using the app model selectors while excluding app/OAuth/API/database settings from its child process. It starts no app/migrations and writes a new ignored report. Its actual cloud invocation reported NOT TESTED/exit 2, not a model pass. Normal app/migration startup is covered by launcher regression tests.

The local-model runner separately reviews nine hash-bound public cases for minimum named-term recall, empty cases and company-background controls. It now reports per-case/overall limited checks separately from valid JSON. Actual native attempt: **9 NOT TESTED**, unknown metrics, exit 2 because no Ollama server/model exists here. No quality pass is claimed; education/experience semantics and exhaustive precision remain unassessed.

## Remaining Phase 2 acceptance work

- Real Ollama execution/quality and independent multi-ATS/positive-date validation at agreed ≥90% field targets, with zero false confirmations.
- Live Lever/Ashby/SmartRecruiters/Reed compatibility and actual official register-file provenance/format checks. Network-only draft approval is pending; no settings were changed/published. Private Mac/API credentials are not available here.
- Adzuna and Find a Job API support are not implemented; Reed is the initial aggregator. Terms/current public contracts must be verified before further adapters.
- Supervised resolution of conflicting pre-existing duplicate histories; current aliases/hints avoid destructive merges. Manual weight tuning is delivered, automatic learning is not.

## Owner start

Stop with Control+C, then from the Mac project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py --migrate
```

Open http://127.0.0.1:3000. Later starts use `python3 scripts/dev.py`. No new project dependencies or Google consent are needed. Optional Ollama/CSV/Reed setup is in docs/SETUP.md; never send keys, OAuth JSON or the private .env through chat.

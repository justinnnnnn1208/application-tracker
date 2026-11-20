# Current project status

Reviewed: 20 November 2026 (Europe/London).

**Phase 2: in progress, roughly 90%.** This estimate is not acceptance. Phase 1 was accepted for progression with the explicit deferrals below. Sheets stays read-only by default; no Phase 3 work, submissions or environment publication.

## Delivered

- Direct charcoal dashboard, job/deadline views, listing links, imported Sheet statuses, profile/CV fact review, worker tasks and opt-in tab-open reminders remain supported. Existing Sheet Notes locally repair missing literal role/location fields and provide a labelled summary fallback. Owner edits, raw snapshots, application history and Notes are preserved.
- Source URLs/official ATS identities retain one job/application for known same-instance posting variants. Global/EU Greenhouse and Lever instances are separate ID scopes. Traceable aliases and conservative fuzzy review hints are visible; two existing histories are never destructively merged or automatically split.
- Local explained preference scores use six criteria and reviewed facts. Active-job batch scoring, highest-current-score sorting, stale detection, Good/Poor feedback and Settings keywords/weights are delivered. Ratings guide manual weight adjustments; no automatic training, sponsorship penalty or legal eligibility inference.
- Greenhouse public board imports were previously verified live with 60 Monzo postings, then zero new/60 duplicates on repeat. Lever global/EU discovery is fixture/integration/browser tested with explicit employer names, bounded pagination, strict listing identity and no partial import after later-page denial. **Live Lever is NOT TESTED:** this cloud proxy blocks its API host. No policy/DNS fallback was changed or bypassed.
- Manual sponsorship findings require an owner-confirmed quote present in saved vacancy description/requirements, a saved listing source and a current context/content fingerprint. Changed role identity/content/location/dates return Unverified; previous evidence remains reviewable/clearable. Notes are not evidence. Validation checks provenance/confirmation, not semantic correctness: the owner reviews the full statement and conditions. Automatic policy assessment and sponsor-register matching remain unfinished.
- Source/review/discovery migrations preserve existing records. `python3 scripts/dev.py --migrate` loads private configuration, refuses a running worker, creates and restores/verifies an existing SQLite DB/storage backup, upgrades the configured database and launches. Behind-schema startup fails with that instruction. No new dependencies; OAuth configuration/encryption keys remain private and unchanged.

## Phase 1 acceptance record

| Criterion | Result | Evidence / remaining limit |
|---|---|---|
| Ten pasted URLs create correct rows | PASSED — controlled fixtures | API → queue → worker → extractor tests. No claim of ten live sites. |
| Re-pasting avoids duplicates | PASSED | Fixtures plus earlier live Monzo repeat; current same-instance aliases retain one application/history. Fuzzy hints do not merge existing records. |
| Sheet preserves all rows | PASSED — owner report + fixtures | Owner confirmed all 20 development-copy rows/data/UI. Current Notes/import tests preserve rows and owner edits. Cloud has no private Mac OAuth session. |
| Only intended status cell changes | NOT TESTED live — explicitly deferred | Single-cell/alias-row/guardrail fixtures pass. No write access enabled or actual Google cells edited this run. |
| Backup restores | PASSED — disposable data | Service/browser/CLI verify DB/facts/CV bytes, including backup-before-migration and custom configured DB. Mac operational restore outstanding. |
| Defaults Unverified unless reviewed evidence | PASSED | API/DB/import/extraction/discovery tests plus explicit review, provenance, stale/legacy rejection and clear tests. Source wording/licences cannot self-confirm. |

Native Mac notification delivery is also outstanding. These accepted deferrals are not passed operational checks.

## Latest verification

- API: **243 passed**, one existing Starlette/httpx deprecation warning. `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short` from apps/api.
- Frontend: `npm run typecheck` and production build passed on the final evidence-clear UI code.
- Final production browser smoke passed on the latest backend/frontend: real disposable worker, Notes repair/restart, identity aliases, score/feedback/weights persistence, evidence save/filter/source/stale/clear, Lever EU source configuration, origin/auth guards, CRUD/history, CV review/download, backup/CLI restore, reminders and 1440/390/320px layouts. No owner data/Google/Lever calls.
- Alembic schema-drift and upgrade/downgrade tests pass; legacy source settings, evidence and job/history preservation covered. Latest head a74cd158ef43.
- Initial new browser failures: ambiguous select labels and an overly exact existing textarea test locator. Corrected; final full runs passed. The first real month-first date failure is retained as evaluation evidence, below.

## Real-page evaluation

Original 30 development snapshots remain frozen. Added five genuine Marshall Wace excerpts, with original visible metadata/header/description and raw/excerpt hashes; forms/scripts/buttons/tracking data excluded. All 35 are on Greenhouse, across five employer labels. Overseas postings are controls, not UK recommendations.

Labels were frozen before the five-case initial held-out prediction at aaebca9. It missed all three explicit “September 6th 2027” start dates (0/3 positive accuracy); the report is retained. Month-first full-date support fixed this and rejects partial/impossible/range dates. The new five cases are now consumed regression/development data, not fresh independent validation.

Both the original 30 and expanded 35 regressions match basic fields and role-level labels. Expanded known coverage: 12 deadlines, 3 exact start dates, 29 graduate-level YES/NO labels. The three date positives share one employer/template. Automatic sponsorship abstains: zero YES/false YES, 4 YES labels, 14 NO labels, zero known-policy accuracy. Unknown matches do not prove evidence quality. Manual-review quality is not measured by this extractor report. **Phase 2 accepted remains false.** See fixtures/eval/REVIEW_NOV19.md and reports/nov19-*.

## Remaining Phase 2 work

Real Lever verification and further ATS/aggregator coverage; automatic structured requirement extraction beyond the finite-keyword heuristic; automatic policy evidence assessment and official sponsor-register provenance; independent multi-ATS/positive-date evaluation; supervised existing-duplicate resolution preserving histories. Existing manual feedback/weight editing is supported, automatic tuning is not. No automatic discovery schedule added.

## Owner start

Stop with Control+C, then from the Mac project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py --migrate
```

Open http://127.0.0.1:3000. Later regular starts use `python3 scripts/dev.py`. No new Google scope/reconnection is needed for these changes. Optional Lever host approval instructions are in docs/SETUP.md; do not send credentials. No owner input is needed for completed work. Live external-source coverage and the deferred Mac checks remain outstanding.

Final UI polish: clearing sponsorship evidence resets the old save acknowledgement and confirmation. Typecheck/build and full production browser rerun passed, including immediate save → clear → confirm again → save. API suite remains 169 passed; no backend change in this polish.

## 20 November checkpoint — local structured requirements

Owner selected local Ollama; qwen2.5:3b recommended as an initial small Mac model, not a verified quality choice. Explicit per-job extraction now produces schema/source-validated technology/education/experience terms with quotes, no tools and no Notes/profile/CV/legal inputs. Only loopback Ollama URLs; bounded context/output/input and three invalid-output attempts. Cached terms are source-bound and revalidated; concurrency/tamper/stale guards fail closed. Current technology terms extend deterministic matching beyond the fixed vocabulary; fallback stays labelled. Education/experience terms are review candidates, not personal qualification decisions.

184 API tests, final frontend typecheck/build and production browser with synthetic loopback Ollama HTTP passed. Browser covers queue → actual worker → schema HTTP contract → quotes → stale score → recalculation. Real 35-page field/classification regression unchanged, zero false YES, phase_2_accepted=false. Actual Ollama execution/semantic quality remain NOT TESTED. Migration b85de269f054 covered by schema/backup/upgrade checks; no new dependencies or private configuration changes. Network-only draft approval is pending; applied settings are unchanged. See docs/decisions/local-requirements.md and SETUP.md.

## 20 November checkpoint — sponsor-register signal

Owner-confirmed, dated CSV import and conservative exact-name signal implemented. Full parsing precedes transactional replacement of public cache only; source/date/hash/raw files retained. Cases/spacing/Unicode composition match, but brands/punctuation/accents/suffixes are not guessed. Policy sponsorship, legal declarations, scores and job/history records remain unchanged. Legacy boolean flags without register provenance are not treated as checks. The UI links the dated source and clearly labels owner-confirmed upload; real official-file/network verification remains NOT TESTED.

207 API tests; frontend typecheck/build; production browser upload through the protected proxy → real worker → separate job signal with Unverified policy; backup/CLI restore including new tables/raw CSV bytes passed. Added migration c96ef370a165. No new dependencies; Sheets/read-only scope and environment settings unchanged. Expanded real-page regression still reports zero extraction failures/false YES and Phase 2 accepted false. Local real-model and live multi-ATS/official-register acceptance remain unverified. Phase estimate ~85% implementation, not acceptance.

## Local-model evaluation runner

Public snapshots plus nine manually reviewed, hash-bound technology expectations now have a standalone local-only runner. It distinguishes schema grounding from semantic minimum-term/empty-case checks and includes company-marketing false-positive controls. It never reads the app DB/profile/Notes/CVs and never overwrites reports. Native endpoint attempt in this cloud returned model unavailable: nine cases NOT TESTED, quality metrics null, exit 2; no semantic pass claimed. All unavailable cases stop after the first failed connection. Unit tests cover abstention, valid-but-wrong category, fabricated output, unavailable server and stale review hashes. API suite 213 passed; no frontend change in this step. Field/classification regression on 35 real snapshots remains unchanged.

## Tier 1 public board coverage and scoring hardening

Ashby adapter/configuration implemented alongside Greenhouse and Lever: listed-only intake, strict board/UUID HTTPS URLs, literal source fields, published-date separation, script-free HTML fallback and owner-preserving same-ID enrichment. No new dependency/schema. Public npm client source inspected for endpoint/field contract, never installed/executed; live official API/docs compatibility still NOT TESTED. Synthetic fixture stays outside genuine eval data.

225 API tests and frontend typecheck/build passed; full production browser passed including disabled Ashby source create/remove and all existing flows. Deterministic scoring now excludes immigration/visa/sponsorship/right-to-work candidates even when misclassified by a model; numeric/fact-citation score invariance test passes. New score version preference-v4-no-immigration-terms invalidates old caches. Initial new assertion compared intentionally different fallback/model explanation strings; corrected to numeric points/citations, then suite passed. Expanded 35-page regression unchanged, zero false YES, Phase 2 acceptance false. No network/config mutation.

## Aggregator / fresh live intake checkpoint

Bounded Reed API keyword search/detail adapter implemented. Private server-only key, readiness boolean only, 20-result page, detailed text, no inferred expiry/deadline dates, official numeric source-ID dedupe and owner-preserving legacy cache migration. Credentials are scoped to exact HTTPS Reed API paths and never sent to robots/URLs/browser/tasks. Existing fetch guards remain. Migration da70f481b276 adds search-query config and generated key repair. 243 API tests; typecheck/build; full production browser passed, including missing-key disabled action and no employer field for search. Live Reed still NOT TESTED: no private key/source grant. No dependencies or environment/private .env mutation.

Fresh permitted public Greenhouse API → actual worker check in disposable DB/storage passed on current code: saved real MW London posting tracked/shortlisted first, API imports 4 new + 1 duplicate; repeat 0 new + 5 duplicates. One application per job, seeded status/two history events preserved, all five Unverified. Current role-only ranking without applicant facts prioritises London graduate role (65) over overseas graduate controls (45). This is a preference demonstration, not personal fit/eligibility. Report fixtures/eval/reports/nov20-live-intake.json; raw API hashes retained, raw captures ignored locally. No Mac DB, Google, portal forms or model requests. Initial temporary script needed PYTHONPATH corrected before it ran; final live check passed.

## Fourth public ATS checkpoint

SmartRecruiters adapter/source controls implemented: first 20 company postings and detailed public text, strict fixed API paths and official company-scoped public listing URLs. Opaque API IDs are distinct from numeric URL identities. Company marketing is excluded from vacancy sections; released dates do not become deadlines. Cached alias-ID migration eb81a592c387 preserves jobs/history. No new dependencies, keys, private configuration or network changes.

**262 API tests**, frontend typecheck/build and full production browser passed, including SmartRecruiters source create/remove, existing local model/register flows and restore. Expanded 35-page regression unchanged; zero extraction failures/false YES and phase_2_accepted=false. SmartRecruiters fixtures are synthetic and do not add real ATS coverage. Live official compatibility remains NOT TESTED. Existing requirement/model and register features are implemented; earlier “unfinished” wording above refers to automatic/live verification, not absence of the current source-grounded task and dated owner-confirmed cache.

## Local transport / discovery queue hardening

Both native requirements and the existing Ollama page provider now enforce loopback endpoints and disable environment proxy routing/redirects. An actual loopback HTTP regression with an unusable shell proxy failed before the fix and passed afterwards. Additional provider tests reject malformed/credentialed/remote bases. Public imports reuse queued/running tasks per source, avoiding repeated-click duplicate work; finished work remains explicitly runnable, disabled/deleted sources still reject. No schedule or automatic retry.

**276 API tests**, production browser and expanded real-page regression passed. Frontend code is unchanged since its passing typecheck/build. Real model quality remains NOT TESTED. README/setup now accurately describe Phase 2 authorisation, owner's confirmed read-only import and the backup-verifying migration launcher; private configuration/Google scopes/network settings unchanged.

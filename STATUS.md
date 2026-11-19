# Current project status

Reviewed: 19 November 2026 (Europe/London).

**Phase 2: in progress, roughly 75%.** This estimate is not acceptance. Phase 1 was accepted for progression with the explicit deferrals below. Sheets stays read-only by default; no Phase 3 work, submissions or environment publication.

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

- API: **169 passed**, one existing Starlette/httpx deprecation warning. `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short` from apps/api.
- Frontend: `npm run typecheck` and production build passed on the latest frontend code; subsequent changes were backend/evaluation only.
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

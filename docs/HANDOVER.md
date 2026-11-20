# Latest session handover — 20 November 2026

**Critical irreversible-action/plan-change question: none.** A network-only draft approval question is pending; do not change settings or publish while it is unanswered. Continue independent work. Owner selected local Ollama and asked to work until **05:00 London time on 20 November** using yesterday's night-shift rules: tested steps, routine decisions documented, working commits pushed; stop early only for critical irreversible action/actual plan change, then write the question at the top.

## Current run

Started at 0a9a1bb on dev/phase-1, clean tree. Environment current/enforced, only the two Greenhouse hosts custom-approved; fresh api.lever.co robots check still CONNECT 403. No network/draft/runtime config was mutated. Read current AGENTS/context/SPEC/STATUS and runtime networking guidance. Pending question proposes adding exact Lever/global-EU, EU Greenhouse and official gov.uk register hosts while preserving existing hosts; no approval received. Local Ollama selected; recommend qwen2.5:3b, real installation/quality untested.

Completed step: local structured requirement extraction. See docs/decisions/local-requirements.md. New migration b85de269f054 adds source-bound public-term cache. Source-only native Ollama /api/chat, no tools, only loopback, schema/quote/token-boundary validation, bounded context/output/retries, concurrency/tamper/stale guards. Never send Notes/profile/CV/legal inputs. Per-job UI task displays terms/quotes; deterministic scoring uses current technology candidates or labelled finite-keyword fallback. No automatic 500-job model batch. Education/experience are candidates, not inferred personal qualifications. Score version changes invalidate old results until recalculation; unrelated-job analysis does not invalidate other scores.

Verification: **184 API tests passed**, one existing deprecation warning; typecheck/build passed; production browser passed through a synthetic loopback Ollama HTTP fixture and real worker (queue, quotes, stale scores/recalc), with all prior security/CRUD/Notes/CV/backup/evidence/discovery/responsive flows. New tests cover privacy, remote endpoint denial, term substrings/ungrounded output, max-three attempts, partial response/input limits, per-job stale/cache behaviour and concurrent source edits. Real 35-page field/classification regression unchanged; zero extraction errors/false YES, Phase 2 accepted false. This does NOT establish real model semantic quality. No new dependencies/private config changes. Phase 2 roughly **80% implementation**, incomplete acceptance.

## Register checkpoint (same run)

Local requirements step pushed as 2b9e6a81052a4505894abb05cc37abe65ae85fcc, remote SHA verified. Next step now complete locally: dated owner-confirmed sponsor CSV cache, exact case/whitespace/Unicode-name lookup, route/town/source/date/hash display, preserved jobs/history/policy/scores. Source provenance is an owner-attested download, not actual online verification. No brand/punctuation/accent/suffix guessing. Uploaded snapshots retained and backed up. Migration c96ef370a165; no dependencies or settings changes.

Checks: **207 API tests passed**; typecheck/build passed; full production browser passed through protected metadata/body upload → real worker → separate register signal, Unverified role policy, and backup/CLI restore of metadata/entries/raw CSV. Final two added legacy/unicode unit cases pass; no runtime changes after browser run. Real 35-page regression unchanged with zero false YES and phase_2_accepted=false. Actual official CSV/live model quality still NOT TESTED. See docs/decisions/sponsor-register.md. Phase 2 ~85% implementation; acceptance incomplete. Network draft approval remains unanswered; do not mutate it.

## Local model runner checkpoint

Register step pushed as 0948974fa32d5b808f4d3e33357588ac1590307e, remote SHA verified. New runner app.services.requirements_eval uses only validated public snapshots and nine manually reviewed/hash-bound technology cases. It reports minimum recall/empty-case/forbidden company-background controls, not complete semantic precision. No DB/profile/Notes/CV access. Existing reports are not overwritten. Real native Ollama attempt failed because no local server/model is installed/running: all nine NOT TESTED, quality metrics null, exit 2; only the first connection was attempted. Do not call this real-model evaluation passed. Unit/API suite 213 passed and 35-case field regression unchanged; no UI changes in this checkpoint. See SETUP.md for the one-command Mac check.

## Ashby / score-neutrality checkpoint

Runner step pushed as 8d40786ac74e23ae255191a43357a268dd5e2e4b, remote verified. Ashby public adapter now complete locally: explicit employer name, listed-only, strict board/UUID job URL, literal locations/dates, no publication-date guessing or private/form calls. 225 API tests, frontend checks and production browser source-config flow passed. Live official source still unverified; third-party public npm source inspected only for contract, not installed/executed. Fixtures synthetic.

Found model-category edge case: source-grounded visa terms could otherwise enter a skill denominator. Added deterministic immigration-term scoring exclusion and preference-v4-no-immigration-terms version. Numeric score/citations remain unchanged with injected visa skill. New test first compared explanation strings that legitimately identify fallback vs local mode; corrected to relevant numeric/citation invariant, then full suite passed. No legal values inferred/changed. Real 35-page field regression unchanged. Network approval still pending; no settings mutated. Next independent source step may add one credential-gated aggregator; real keys must be configured privately, never requested in chat.

## Reed / fresh live checkpoint

Ashby/scoring step pushed as 9bc3e1f1f9159356f599bd9bad02a24e821d1fef, remote verified. Reed aggregator now implemented with private REED_API_KEY, bounded first-20 search plus detailed API text, exact official ID/URL checks, credential-free robots and strict credential path scope. Source readiness bool only; no browser key input. Migration da70f481b276 preserves old source config and reindexes cached Reed URLs without history merges. 243 API tests, frontend and full browser passed, including absent-key/source configuration. Synthetic fixture key only; real Reed source/key unavailable. No private .env/network changes.

Fresh allowed Greenhouse live API/worker check also passed in temporary storage: pre-seeded/shortlisted genuine MW London posting → 4 new/1 duplicate → repeat 0 new/5 duplicate; one application per job, seed status/two events preserved, all Unverified. No facts/profile/model/Google/portal forms. London grad preference score 65, overseas controls 45 with no applicant facts. Saved public metadata report fixtures/eval/reports/nov20-live-intake.json; raw API responses ignored .local/live-nov20. Temp script's module path fixed with PYTHONPATH before execution; no app regression. Phase 2 ~90% implementation, acceptance still incomplete; real Ollama/blocked-source/official register verification remains pending. Next work can harden proof/remaining source scope while waiting; do not publish the unanswered network draft.

## SmartRecruiters checkpoint

Reed/live step pushed as 35bb6cb5d98a5c1f9bb879e34f755a7a0bcd5f93, remote verified. Fourth public ATS now implemented: bounded first-20 company page plus detailed text, strict company/public numeric listing identity distinct from opaque API ID, no arbitrary ref/form URLs. Migration eb81a592c387 backfills cached identities, preserving jobs/history. 262 API tests, typecheck/build, full production browser passed; expanded 35-real-page regression unchanged. Fixtures are synthetic; official live compatibility remains NOT TESTED. No settings/private config/dependencies changed. See decisions/smartrecruiters-discovery.md.

## Local transport / queue checkpoint

SmartRecruiters pushed as e11e53523cd025076472ab4403372c18a00bafb9, remote verified. Both Ollama paths now validate loopback endpoints and ignore shell proxies/redirects; new direct-loopback test reproduced failure before the fix and passed after. Pending discovery requests reuse one source task; completed imports may be requested again. 276 API tests, full production browser and expanded real-page regression passed; frontend unchanged since its passing checks. README/setup corrected stale phase/import/migration statements. No dependencies/private settings/network changes. Real model quality still NOT TESTED.

## Real controls / source-validation checkpoint

Local transport/queue step pushed as 0c71da6473768f3c90696184013659d6f6e14ba1, remote verified. Three new genuine GoCardless excerpts manually labelled/frozen before prediction; initial fields/role controls correct, 3-case probe exit 2 only for size below 30. New manifest-nov20.json has 38 real pages/six employer labels, all Greenhouse; old 30/35 frozen. No new positive dates/policy labels; future runs are regressions. Initial evidence/provenance retained. See fixtures/eval/REVIEW_NOV20.md.

Live metadata reads revealed custom employer URLs and EU-hosted listings returned by the shared Greenhouse API; no blocked host was fetched or settings changed. Source hardening now rejects malformed IDs/content and mismatched known Greenhouse board/ID URLs, retains custom links without inferring identity from their query params, and respects EU URL scope. Initial seven defect tests failed before fix; one extra malformed-content case failed later, then corrected. Final 289 API tests passed. Browser and fresh strict-ID live disposable import/repeat passed; current 38-page regression exit 0, phase_2_accepted=false. Current model runner now separates valid JSON from limited-content checks; actual native attempt still all nine NOT TESTED/exit 2. No real model quality pass. STATUS/README/setup consolidated to remove stale statements.

## Backup preservation checkpoint

Real-controls/source step pushed as 78eb45ec186671e60f78de71fdef9f615eb6b81f, remote verified. Restore review reproduced acceptance of missing-database/unsupported/duplicate-member archives; now rejects before any restored destination. Valid version-1 format preserved. Exact database snapshots now encode SQLite file URIs: # could previously select/create a different empty file, percent escapes could open the wrong path/fail. Three filename regressions prove app-driver and restored-row identity/no truncated file. First percent fixture used an incorrectly encoded SQLAlchemy URL; corrected to URL.create/render_as_string, same assertions retained. Final 298 API tests and production browser backup/CLI restore passed. No schema/dependencies/private data/config changes. See decisions/backup-manifest-validation.md. Mac operational restore remains untested.

## One-command Mac model check

Backup step pushed as 953ea676a1942b6996f1455961897ce271d9dc06, remote verified. Existing launcher now supports `python3 scripts/dev.py --check-model` from root: same private model selectors/shell precedence, minimal child environment excluding app/OAuth/API/database settings, no app startup/migration, unique ignored report. Mutually exclusive with --migrate. Five tests cover privacy/setup/exit/conflict and preserved normal/migration startup; full suite 303 passed. Actual shortcut reached native unavailable endpoint, all nine NOT TESTED/exit 2, report .local/requirements-check-174d887a51c647619e12293350d080a5.json. No real model quality pass. Backend/frontend unchanged; previous browser/build evidence remains applicable. See SETUP.md.

## Continue next

Push the checked launcher shortcut, verify remote SHA, then finish the acceptance/readiness review and morning handover until 05:00. Real Lever/Ollama/multi-ATS checks remain blocked/unverified. Do not enable writes/submit or start Phase 3. Keep Phase 1 deferrals below visible. Use backup-verifying `python3 scripts/dev.py --migrate` after pulling these migrations; private Ollama setup is in SETUP.md. End with the requested 05:00 summary, not the older 02:45 cutoff below.

## Prior run / Phase 1 acceptance record

## Previous session handover

**Critical question: none.** No irreversible action or plan change is required for the completed work. Live Lever remains blocked by this cloud's proxy; no network grants were changed/published or bypassed.

## Session

19 November 2026, Europe/London. Owner requested continued Phase 2 work until **02:45**, tested steps, routine decisions documented, working commits pushed, then a short morning summary. Phase 2 is approximately 75%, incomplete; Phase 1 progression was explicitly accepted with operational deferrals. Phase 3 is not authorised. Sheets stays read-only by default. No hosted processing of personal data, forms/submissions or original Sheet access.

Repository: justinnnnnn1208/application-tracker, dev/phase-1. Owner Git identity remains configured; no history rewrite. Started this run at faff611 with a clean tree. Uploaded academic-feedback skill files remain reference material, not installed/applied instructions.

## Finished / verified

| Work | State / reference | Evidence and limits |
|---|---|---|
| Manual sponsorship review | Complete, 5bc6444; docs/decisions/manual-sponsorship-evidence.md | Quote in saved vacancy text, saved source URL, explicit owner confirmation and context hash. Stale/legacy evidence returns Unverified; clear supported. Semantic judgement remains the owner's; no automatic classifier/licence check or score/legal change. |
| Lever global/EU discovery | Complete adapter, b707a6e; docs/decisions/lever-discovery.md | Contract/worker/API/browser tests: bounded pagination, no partial import, listing/board/UUID checks, explicit employer name, dedupe vs pasted apply URL. Synthetic fixtures are not real eval pages. Live API blocked/unverified. |
| Region identity isolation | Complete, aaebca9 | Global/EU namespaces separated for Lever/Greenhouse; cached keys migrate without changing job/history relationships. Same-instance aliases dedupe. Previously combined records are not split automatically. |
| Real exact-date regression | Complete and verified, included in this delivery | Five genuine MW excerpts; labels frozen before prediction. Initial 0/3 exact-date failure retained; month-first correction now passes all three. Two flexible ranges remain null. The fix consumes these cases as regression data, not new independent held-out evidence. |

Earlier deliveries f062f01 and faff611 provide aliases/fuzzy hints, backup-verifying migrations and manual matching weights/feedback counts. Notes repair/ranked lists came before them. No new dependencies added tonight.

## Checks

- **169 API tests passed**, one existing Starlette/httpx deprecation warning. Run from apps/api: `UV_CACHE_DIR=/tmp/tracker-uv-cache uv run --frozen pytest -q --tb=short`.
- Latest frontend typecheck/build passed on the final UI code.
- Final production browser smoke passed with disposable DB/storage and a real worker, including evidence consent/save/source/filter/invalidation/clear, weights persistence, Lever EU source settings, source aliases, Notes repair/restart, core security/CRUD/history, CV, backup/CLI restore, reminders and responsive layouts.
- Migrations/schema drift pass. Latest head **a74cd158ef43**. Upgrade/downgrade preserves legacy data/settings/evidence; cached EU-key repair does not rewrite histories. New startup must use `--migrate` below.
- Original 30-case regression unchanged; expanded 35-case regression matches basic/role labels and 3/3 exact start dates. Five employer labels, one ATS; all three date positives share one template. Source/form stripping and raw/excerpt SHA provenance recorded.
- Initial five-case held-out date failures are retained in fixtures/eval/reports/nov19-initial-heldout.json. Subsequent reports are regressions, not fresh independent validation. All reports keep phase_2_accepted=false. Automatic sponsorship known-label accuracy remains zero due to abstention; zero false YES is not evidence-assessment quality.
- First browser failures were select-label ambiguity and an over-exact textarea locator; fixed and full flow rerun successfully. No unresolved application-test failure at this checkpoint.

## Phase 1 acceptance

| Criterion | Result | Verification / remaining limit |
|---|---|---|
| 10 URL imports correct | PASSED — fixtures | API/queue/worker/extractor; ten live sites not claimed. |
| Repeat intake no duplicates | PASSED | Fixtures and earlier live Monzo 60 → zero new/60 duplicate repeat; aliases preserve one application. |
| All Sheet rows preserved | PASSED — owner + fixtures | Owner confirmed 20 rows/data/UI. Current import/Notes tests preserve edits/history. No private Mac OAuth access here. |
| Intended single-cell write | NOT TESTED live — deferred | Guards/alias-row fixtures pass; writes remain disabled by default. No Google cells edited. |
| DB/storage restore | PASSED — disposable | Service/browser/CLI exact DB/facts/CV bytes and migration backups. Mac operational restore untested. |
| Default Unverified | PASSED | API/DB/import/extraction/discovery; confirmed findings require explicit owner review and current evidence. |

Native Mac notification delivery remains untested. Keep these accepted deferrals visible; do not mark Phase 1 universally verified.

## Remaining / resume

1. Read AGENTS.md, context, SPEC, STATUS and this handover; inspect Git/environment. Preserve local data and owner authorship.
2. Verify a real Lever board once network access is available. Cloud currently blocks api.lever.co (CONNECT 403); do not bypass it or reapply/publish environment settings without a new owner instruction. Mac host opt-in and cloud network policy are separate. Existing public GitHub docs were used only for the GET contract.
3. Continue official sponsor-register/evidence work and structured requirements beyond finite-keyword matching. Sponsorship remains informational, never a filter/score penalty. Never infer visa eligibility or change legal declarations.
4. Add independent multi-ATS and diverse exact-date positives before claiming accuracy generalises. Current consumed date cases/initial failures are documented in fixtures/eval/REVIEW_NOV19.md. Existing two-history merge requires a supervised preservation design; do not delete/merge histories automatically.
5. Update docs, test each completed step, push dev/phase-1 and verify the remote SHA. No Phase 3 or Sheets writes authorised by this night shift.

## Morning start — small enough for coffee

Stop the app with **Control+C**. In the Mac project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py --migrate
```

Open **http://127.0.0.1:3000**. The launcher backs up/restores-verifies existing configured SQLite DB/storage before applying migrations, and refuses a running worker or failed backup. Keep the encryption key separately; `.env` is preserved. No new dependency install or Google permission is required.

Try Settings → Matching preferences; job details → Review role-specific evidence. Leave unclear policy Unverified. Lever source setup is optional and requires the correct API host/region/employer; live coverage is not yet verified. Existing imported Notes are preserved and repair locally on restart, without another Sheet import.

Owner input: **none needed for delivered work**. Future live-source access and deferred Mac operational checks remain outstanding. Date/parser/evaluation delivery eb212d9fcd70f43b363ec0071ea9557213b0598b was pushed and its full SHA matched GitHub dev/phase-1. Final UI clear-message polish passed typecheck/build and a full production browser rerun that saves, clears immediately, checks removal of the old saved message/confirmation, and saves again. Included in the final delivery commit. Ignored raw captures/logs/screenshots remain local; generated next-env.d.ts drift is excluded. No credentials, private data or source forms/scripts are committed.

## Final delivery checkpoint

Final application commit **f18023bc2619c83b2a7838b716c73b35e0be00bf** was pushed to dev/phase-1 and its full SHA matched the GitHub branch. This documentation-only follow-up records that verification. The final application checks are 169 API tests, frontend typecheck/build and the full extended production browser flow, all passed. New-page sanitisation and staged private-value checks passed without printing credentials. No Sheets/OAuth/core-security files changed from faff611 during this run; read-only scope and guards remain intact. No unfinished runtime edits remain; ignored raw public captures/logs/screenshots are local only.

Cutoff requested by owner: 02:45 London time on 19 November 2026. No further feature work is planned before that summary. Resume with the five steps above; full Phase 2 acceptance remains incomplete.

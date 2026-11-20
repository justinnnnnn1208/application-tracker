# Latest session handover — 20 November 2026

**Critical irreversible-action/plan-change question: none.** A network-only draft approval question is pending; do not change settings or publish while it is unanswered. Continue independent work. Owner selected local Ollama and asked to work until **05:00 London time on 20 November** using yesterday's night-shift rules: tested steps, routine decisions documented, working commits pushed; stop early only for critical irreversible action/actual plan change, then write the question at the top.

## Current run

Started at 0a9a1bb on dev/phase-1, clean tree. Environment current/enforced, only the two Greenhouse hosts custom-approved; fresh api.lever.co robots check still CONNECT 403. No network/draft/runtime config was mutated. Read current AGENTS/context/SPEC/STATUS and runtime networking guidance. Pending question proposes adding exact Lever/global-EU, EU Greenhouse and official gov.uk register hosts while preserving existing hosts; no approval received. Local Ollama selected; recommend qwen2.5:3b, real installation/quality untested.

Completed step: local structured requirement extraction. See docs/decisions/local-requirements.md. New migration b85de269f054 adds source-bound public-term cache. Source-only native Ollama /api/chat, no tools, only loopback, schema/quote/token-boundary validation, bounded context/output/retries, concurrency/tamper/stale guards. Never send Notes/profile/CV/legal inputs. Per-job UI task displays terms/quotes; deterministic scoring uses current technology candidates or labelled finite-keyword fallback. No automatic 500-job model batch. Education/experience are candidates, not inferred personal qualifications. Score version changes invalidate old results until recalculation; unrelated-job analysis does not invalidate other scores.

Verification: **184 API tests passed**, one existing deprecation warning; typecheck/build passed; production browser passed through a synthetic loopback Ollama HTTP fixture and real worker (queue, quotes, stale scores/recalc), with all prior security/CRUD/Notes/CV/backup/evidence/discovery/responsive flows. New tests cover privacy, remote endpoint denial, term substrings/ungrounded output, max-three attempts, partial response/input limits, per-job stale/cache behaviour and concurrent source edits. Real 35-page field/classification regression unchanged; zero extraction errors/false YES, Phase 2 accepted false. This does NOT establish real model semantic quality. No new dependencies/private config changes. Phase 2 roughly **80% implementation**, incomplete acceptance.

## Register checkpoint (same run)

Local requirements step pushed as 2b9e6a81052a4505894abb05cc37abe65ae85fcc, remote SHA verified. Next step now complete locally: dated owner-confirmed sponsor CSV cache, exact case/whitespace/Unicode-name lookup, route/town/source/date/hash display, preserved jobs/history/policy/scores. Source provenance is an owner-attested download, not actual online verification. No brand/punctuation/accent/suffix guessing. Uploaded snapshots retained and backed up. Migration c96ef370a165; no dependencies or settings changes.

Checks: **207 API tests passed**; typecheck/build passed; full production browser passed through protected metadata/body upload → real worker → separate register signal, Unverified role policy, and backup/CLI restore of metadata/entries/raw CSV. Final two added legacy/unicode unit cases pass; no runtime changes after browser run. Real 35-page regression unchanged with zero false YES and phase_2_accepted=false. Actual official CSV/live model quality still NOT TESTED. See docs/decisions/sponsor-register.md. Phase 2 ~85% implementation; acceptance incomplete. Network draft approval remains unanswered; do not mutate it.

## Continue next

Push the checked register step and verify the remote SHA, then continue the independent real-model evaluation runner/public-source adapter work. Real Lever/Ollama/multi-ATS checks remain blocked/unverified. Do not enable writes/submit or start Phase 3. Keep Phase 1 deferrals below visible. Use backup-verifying `python3 scripts/dev.py --migrate` after pulling this migration; private Ollama setup is in SETUP.md. End with the requested 05:00 summary, not the older 02:45 cutoff below.

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

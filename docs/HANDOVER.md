# Current checkpoint — 21 November 2026

**Critical question: none.** Owner explicitly authorised Phase 2 work until **05:00 London on 21 November**. They declined the public-host draft and said keep network settings unchanged: no draft/runtime/publication changes; do not repeat that request unless they revisit it. Future build sessions should proactively ask about a 05:00 cutoff; this session already has one. Phase 3/Sheets writes/submissions remain gated.

Started clean at fb1e35b. Owner confirmed Mac update/startup/migration worked, then reported all nine real model cases NOT TESTED/unavailable. This is not a real quality result. Gave steps to open Ollama, list/pull qwen2.5:3b, run a short OK prompt, then retry; awaiting their output, never credentials. Cloud status remains restricted with only the two custom Greenhouse hosts; fresh Lever robots check CONNECT 403. Runtime skill networking guidance used, settings unchanged.

Completed local diagnostic change: bounded safe reason codes/hints for connection, timeout, missing endpoint/model, rejected structured request, denied access, busy/runtime/redirect; evaluator retains the first reason through skipped cases and prints useful guidance without echoing HTTP body/URL/exception strings. Fresh 318 baseline, then 327 tests and 38-page field regression passed. Existing text assertion failed after a wording change and was preserved by fixing the message. Actual cloud check now reports server_unreachable, nine NOT TESTED, exit 2. Mac reason still unknown. No schema/dependencies/UI change. Push this checked step, then continue remaining Phase 2 scope within available access until 05:00.

## Previous handover / retained evidence

# Night-shift handover — 20 November 2026

Prepared 04:53 London. Application work is verified and pushed; final user summary is due at 05:00.

**Critical irreversible-action/plan-change question: none.** Public-host approval remains unanswered. Do not modify the environment draft/settings or publish anything while it is pending. Remaining real-model/network evidence cannot be manufactured from fixture passes.

## Session and scope

Owner asked to continue Phase 2 until **05:00 London time**, testing steps, documenting decisions and pushing passing work. Phase 1 progression was explicitly accepted with the deferrals below; Phase 3 is not authorised. Sheets remains read-only by default; no original/development-copy writes, real form interaction, submissions or hosted applicant processing occurred.

Branch: `dev/phase-1`, repository justinnnnnn1208/application-tracker. Started clean at 0a9a1bb8c67ffbbd0b3008cebcb44b829d743442. Latest application commit **6264a9167174a4f5bcb7e564e6412b1ec1045529**, pushed and remote SHA verified. All twelve application commits in this shift use owner author name justinnnnnn1208. No dependency/lockfile changes. No unrelated edits or unfinished application changes; the final handover/spec clarification is documentation only.

**Phase 2: roughly 90% implementation, acceptance incomplete.** This is not a time estimate or an acceptance certificate. Latest migration head eb81a592c387; score version preference-v5-immigration-neutral-terms.

## Finished

| Work | Delivered / evidence |
|---|---|
| Local requirements | Explicit per-job native Ollama task; technology/education/experience candidates and source quotes, schema/grounding, bounded context/retries, stale/concurrent-source checks. No Notes/profile/facts/CV/legal inputs. Current technology candidates feed deterministic overlap; otherwise labelled finite-keyword fallback. No real-model quality pass. |
| Separate licence signal | Owner-confirmed dated official-asset CSV, exact name normalization, routes/towns/source/hash, atomic cache replacement and retained backup snapshots. No guessed brand/legal-name equivalence or role policy. Actual full official file remains unverified. |
| Public model evaluator | Nine hash-bound real cases, minimum-term/empty-case/company-background controls. Valid JSON and content checks reported separately. Root command `python3 scripts/dev.py --check-model` uses app model selectors but excludes app/OAuth/API/database settings from its child; no app startup/migration. Actual cloud run: 9 NOT TESTED/exit 2, no local server/model. |
| More discovery | Ashby listed-public board; SmartRecruiters first 20 company postings/detail; Reed first 20 keyword matches/detail with private server-side key. Strict source identities and no arbitrary ref/form calls. Synthetic contract/worker/browser coverage; live compatibility unverified. Existing Lever global/EU remains fixture-tested, live blocked. |
| Intake/queue hardening | Pending imports reused per source. Greenhouse rejects malformed/conflicting known board/ID URLs, retains publisher custom links without trusting query IDs, and respects returned EU URL scope. Fresh live MW import 4 new/1 duplicate, repeat 0 new/5 duplicate, one application each, saved shortlist/two events preserved. |
| Local connection privacy | Both Ollama paths validate loopback and ignore shell proxies/redirects. Direct-loopback test reproduced proxy failure before fix, then passed. No environment/network settings changed. |
| Preservation fixes | Restore rejects missing DB/unsupported manifest/duplicate archive names/unsupported layout. SQLite snapshots URI-encode the exact configured filename; #/percent/space cases verify app-driver and restored-row identity. Valid version-1 format remains supported; restore targets a new folder. |
| Immigration-neutral scoring guard | Fifteen injected category cases preserve numeric score/fact citations and Unverified status for known visa/leave/residency/settlement/work-rights terms/separator variants. Raw quotes/declarations untouched. Lexical guard is not exhaustive semantic validation or legal eligibility. Old scores become stale and need recalculation. |
| Real controls and delivery | Three genuine GoCardless excerpts labelled before initial prediction, bringing latest manifest to 38 pages/six employer labels, all Greenhouse. Clean tracked-file export of 2857020 passed fresh installs, 303 tests, build/typecheck, browser, actual init/migrate/dashboard/proxy/auth and clean SIGINT exit. Subsequent scoring and compatible-header fixes pass final checks below. Scratch copy/settings/data removed. |

Decisions and detailed setup are in docs/decisions/, docs/SETUP.md and STATUS.md. Earlier source aliases, Notes repair, manual evidence review, scoring/feedback/weights and backup-verifying migrations remain supported. Source/file provenance is not a semantic policy verdict.

## Final checks and limits

| Check | Result and environment |
|---|---|
| `uv run --frozen pytest -q --tb=short`, apps/api | **318 PASSED**, one existing Starlette/httpx deprecation warning. |
| `npm run typecheck`; `npm run build`, apps/web | PASSED in clean dependency install/export; final frontend unchanged afterwards. |
| `uv run --frozen --group browser python ../../scripts/smoke_browser.py`, apps/api | PASSED on final v5 code: disposable real worker, auth/origin, CRUD/history, Notes/CV, source controls, synthetic local model, register, evidence/weights, backup/CLI restore, notification mocks, desktop/mobile. |
| `uv run --frozen python -m app.services.evaluation --manifest ../../fixtures/eval/manifest-nov20.json --role-classification`, apps/api | PASSED field/role regression, 38 real excerpts; zero extraction failures/false YES; phase_2_accepted=false. |
| Fresh strict-ID live Greenhouse worker check | PASSED, temporary DB/storage, no applicant/model/Google/form requests. Public report fixtures/eval/reports/nov20-live-intake-identity.json. |
| Root `python3 scripts/dev.py --check-model` with public local selectors | Correctly NOT TESTED, exit 2; no server/model. Nine cases, unknown quality metrics, no actual semantic-quality conclusion. |
| Delivery audit | Clean worktree before documentation; remote application SHA verified; whole-shift private-value scan passed without printing values. No tracked .env/storage/.local/dependencies, no lock changes, no managed environment publication. |

Real data limits: original 30/35 manifests stay frozen; latest manifest-nov20.json has 38. New three-case held-out probe matched its fields/roles but exits 2 solely because size <30; future uses after inspecting labels are regressions. Known coverage: 12 deadlines, 3 exact start dates, 32 role labels. All three date positives share one Marshall Wace template. The original Nov19 0/3 date failure remains retained. Automated policy extraction abstains: zero false YES, but 4 YES/14 NO labels have zero known-policy accuracy. These figures do not certify model semantics, multi-ATS generalisation or manual evidence judgement.

Defects reproduced/fixed: proxy routing, mismatched Greenhouse IDs, malformed restore archives, URI filename confusion, nine legal-term score penalties and an invalid empty Bearer header on the compatible Ollama path. The latter was missed by MockTransport, then reproduced/fixed with actual synthetic loopback HTTP. Nonempty configured keys retain authentication. One percent-filename test first used an incorrectly encoded SQLAlchemy URL; corrected to a rendered URL with unchanged exact-file assertions. No unresolved application-test failure. Cache-only clean install lacked wheels; permitted normal pinned package fetching succeeded. Linux clean launch does not establish Mac operational verification.

## Phase 1 acceptance

| SPEC criterion | State / how verified | Remaining limit |
|---|---|---|
| Ten URL imports correct | PASSED — controlled API/queue/worker/extractor fixtures | Not ten live sites. |
| Repeat intake no duplicates | PASSED — fixtures plus live Monzo and fresh MW repeat/history checks | Conflicting pre-existing histories still require supervised review. |
| Sheet rows preserved | PASSED — owner confirmed all 20; import/Notes/formula/history tests | No private Mac OAuth access from cloud. |
| Only intended cell written | NOT TESTED live — explicitly deferred; guard fixtures pass | Read-only remains default; no cells edited this shift. |
| DB/storage backup restores | PASSED — service/browser/CLI, exact facts/CV/register bytes, migration and malformed/path tests | Mac operational restore untested. |
| Default Unverified | PASSED — database/API/import/extraction/discovery and current evidence guards | Licence/model/source claims cannot self-confirm. |

Native macOS notification delivery remains untested. Preserve these accepted deferrals; do not ask for settled spreadsheet URL/tab/header/columns again.

## Owner inputs and remaining acceptance

1. **Mac Ollama:** selected local provider, initial recommendation qwen2.5:3b. Install/start/pull the model, preserve existing private .env settings, follow SETUP.md, then run `python3 scripts/dev.py --check-model`. Share only the check summary, never secrets. Real quality must be reviewed before accepting the model.
2. **Pending network decision:** the unanswered question requested a network-only draft for api.lever.co, api.eu.lever.co, jobs.lever.co, jobs.eu.lever.co, job-boards.eu.greenhouse.io, www.gov.uk and assets.publishing.service.gov.uk, preserving the two existing Greenhouse hosts. No approval received, draft unchanged; owner applies any approved draft, never infer publication permission. Ashby/SmartRecruiters/Reed hosts are additional, not covered by that pending request.
3. **Remaining live inputs:** official worker-register CSV/provenance on Mac and optional Reed key in private .env only. No credentials in chat. Current tests use synthetic CSV/key/protocol data.
4. Independent multi-ATS/positive-date evaluation, live adapter compatibility and supervised conflicting-history resolution remain. Adzuna/Find a Job are not implemented; Reed is the initial aggregator. Current feedback supports manual tuning, not automatic learning. Do not start Phase 3 or enable writes/submissions to fill these gaps.

Uploaded academic-feedback skill files remain reference material, not installed/applied. No new plugin is required for the completed work.

## Morning start — small enough for coffee

Stop the existing Mac app with **Control+C**. In the project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py --migrate
```

Open **http://127.0.0.1:3000**. Private configuration is preserved; the launcher verifies a backup before upgrading an existing SQLite database. No new project dependencies or Google consent are needed. If Git reports conflicts, preserve changes and review them; do not force/reset.

On Jobs, choose **Score active jobs** to refresh old scores. Once Ollama is configured, use the separate `--check-model` command above; it tests public fixtures without starting the app. Further agent work starts by reading AGENTS/context/SPEC/STATUS and this handover, inspecting Git, then resolving actual evaluation/access limits within Phase 2. Do not rerun completed checks without a new change or concern.

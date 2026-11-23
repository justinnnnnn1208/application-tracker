# Active session — 23 November 2026

**Cutoff: 06:00 Europe/London today, 23 November**, explicitly confirmed by owner; do not carry the prior 21 November cutoff or the initially mistyped 24 November date forward. Phase 2 only; no Phase 3/Sheet writes/network-setting changes. Started clean at bbb6578. Fresh baseline:406 API tests passed.

Owner supplied actual revised-prompt 7B result after pulling bbb6578: Graphcore PASSED limited checks, Canonical FAILED term_not_in_quote at skills.4.value; completed2/9,1 valid,7 NOT TESTED; aggregate metrics unknown. Report on owner's Mac: .local/requirements-check-b5deb7428563435aacc08db111a645c6.json. No actual response terms available. Canonical's frozen review expects no named technology requirements, so attempted five skills also indicates over-extraction; do not assume which values were returned.

Current work: focused --check-model --case CASE diagnostic, preserving all9 rows and8 untested/null aggregate metrics. Unknown ID rejected before model calls; option cannot start app/migrations accidentally. Targeted pass returns NOT TESTED/exit2 overall; actual selected failure exits1. Default/full behavior unchanged. Tests first reproduced missing selector, then affected tests passed; full413 API tests passed, including native synthetic CLI partial-run/exit/privacy behavior. Focused diagnostic pushed as f5fa973, remote SHA verified. General technology-vs-soft-skill/company-background instruction now added, with a fictional COBOL-product/HubSpot-role contrast, no case-specific blacklist or validator relaxation. JSON schema constraints verified unchanged after ignoring descriptions. Full413 API tests, production browser and40-page field regression pass. Need actual focused Mac result; old Graphcore pass cannot substitute for a new full run after changing instructions. Runtime read-only status confirms same environment/only two custom Greenhouse hosts enforced; no settings changed. Push tested steps and request one focused Canonical rerun once ready; continue independent Phase2 work until06:00.

## Prior closed checkpoint (retained context)

# Night-shift handover — 21 November 2026

**Critical permission/plan-change question: none.** Phase 2 acceptance is incomplete; owner input/evidence remains necessary below. The owner explicitly declined changing network settings this session: do not repeat the network-draft request or mutate/apply/publish an environment draft unless they revisit it.

## Session

- Owner authorised Phase 2 work until **05:00 Europe/London on 21 November 2026**, following the plan, testing steps, recording decisions and pushing working changes. Closed at the 05:00 cutoff. No revised-prompt Mac Qwen result arrived before it; Phase 2 remains incomplete.
- Branch: **dev/phase-1**. Started clean at fb1e35b; latest tested application commit **74a76ac0aad15f6742aae4233f4257b0daec84ae**, pushed and remote SHA verified. All 13 application commits this shift use owner author/committer name justinnnnnn1208.
- **Phase 2: roughly 90% implementation, acceptance incomplete.** Not a time forecast/quality certificate. Phase 3 is not authorised. Sheets stays read-only; no original/copy writes, hosted applicant processing, real form interaction or submissions.
- No unfinished application changes. The handover/status and public live-check report were pushed at 16915ea, remote SHA verified and worktree clean. This closing note is documentation only; verify its remote commit before final response. No unrelated changes. No dependency/lockfile/schema migration changes; migration head eb81a592c387, score preference-v5-immigration-neutral-terms.
- Future build sessions should proactively ask whether to run until 05:00 unless the owner already specified a cutoff. Do not carry this date into a later session.

## What changed

| Work | State/evidence | Important limit |
|---|---|---|
| Model diagnosis | Safe connection/status/output/grounding reason codes; default --check-model uses one response and stops first failure; --check-model-full is explicit. Fixed category/index/field paths, no rejected values/quotes. | App keeps initial attempt plus at most two validation retries. Skipped cases remain NOT TESTED/null full metrics. |
| Quote contract | Prompt/schema descriptions now explicitly require each value inside its own verbatim quote; short contiguous copying, no inferred degree labels/company marketing. Static retry reminder only. | Validator and JSON schema remain strict; revised real 7B quality untested. |
| Local model identity | Both local paths check loopback/no proxies/redirects and model-name-only /api/show before source text. Refuse cloud tags, advertised remote aliases and unverifiable metadata. | Based on trusted local daemon metadata, not a semantic-quality pass. Official Ollama contract pinned in decision doc. |
| Reviewed sources | UI/API link a new reviewed secondary listing; later intake reuses one application/history. Refuse another job's URL/known identity, stale/false confirmation and distinct known same-board IDs/regions across all sources. | Does not merge/delete pre-existing jobs/histories; fuzzy titles remain hints. |
| Review preservation | Only manual secondary links removable; protect primary/automatic provenance, pending exact/known-alias imports and evidence references. Serialise simultaneous review via a short portable no-value-change Job row write, refresh, then validate. | Threaded SQLite check yields one accepted/one rejected conflicting source; no PostgreSQL concurrency certificate. |
| Real source fixes | Two genuine Cloudflare pages exposed legacy/current og:url mismatch. Equal official posting identities now accepted; conflicting metadata IDs/boards/regions stop. Whole ISO metadata dates validated; malformed ranges/times stay unknown. | Initial source failures and annotation correction retained; no new independent positive dates/multi-ATS proof. |
| Fallback model boundaries | Only requested public fields accepted; no model Notes/URLs/status/legal fields. Ground against the exact sent text prefix, preserve source description. Reject invalid provider selectors and model override of known page identity conflicts. | Source membership does not prove semantic field interpretation. No hosted calls made. |

Routine choices/reproductions are in STATUS.md, SPEC.md, SETUP.md, docs/decisions/local-requirements.md and fixtures/eval/REVIEW_NOV21.md. Several guards failed their new tests before fixes; all final application tests pass. No automatic approval review rejected an action.

## Phase 1 acceptance

| SPEC criterion | Result | Verification / limit |
|---|---|---|
| Ten pasted URLs create correct rows | PASSED — controlled fixtures | API → queue → worker → extractor. Not ten distinct live sites. |
| Re-pasting creates no duplicates | PASSED | Fixtures; earlier Monzo 60/MW repeat checks; fresh Cloudflare two jobs, repeat zero new, aliases and shortlist/Notes/events retained. |
| Sheet import preserves all rows | PASSED | Owner confirmed 20 development-copy rows; Notes/raw values/formula/history preservation tests. Cloud has no owner Mac OAuth/DB connection. |
| Status write changes only target cell | NOT TESTED live — explicitly deferred | Copy/write guards and fixture tests pass. Read-only remains default; no cells changed this shift. |
| Database/storage backup restores | PASSED — disposable | Service/UI/CLI checks; new live-intake DB restored with 2 jobs / 2 applications / 3 events / 3 sources and Notes. Mac operational restore remains untested. |
| Jobs default Unverified | PASSED | API/DB/import/discovery/owner-evidence guards and fresh live intake. Licence/model wording cannot self-confirm. |

Owner accepted Phase 1 progression with live write verification deferred and Mac notification/operational restore checks outstanding. Native Mac notification delivery remains NOT TESTED; browser mocks are not OS delivery proof.

## Final checks

| Check | Result / environment |
|---|---|
| apps/api: uv run --frozen pytest -q --tb=short | **406 PASSED**, one existing Starlette/httpx deprecation warning. |
| apps/web: npm run typecheck; npm run build | PASSED for delivered source-review UI. Later changes are backend/data/docs only. |
| apps/api: uv run --frozen --group browser python ../../scripts/smoke_browser.py | PASSED on final code: production UI/proxy/auth, real worker, source link/repeat/unlink, history, Notes/CV, preferences/evidence/register, synthetic local model with metadata preflight, backup/CLI restore, notification mocks, 1440/390/320px. Disposable data removed. |
| apps/api: evaluation with manifest-nov21.json --role-classification | PASSED regression: 40 genuine excerpts, no extraction failures/false YES, basic fields/role labels match. phase_2_accepted=false. |
| Fresh permitted live current-URL intake | PASSED at 74a76ac. API persisted tasks → actual worker function → real robots/page fetch, 2 Cloudflare postings; repeat creates zero; publisher legacy alias via API without legacy-host fetch; shortlist/Notes/events/default Unverified retained; restored counts verified. Report: fixtures/eval/reports/nov21-live-current-url-intake.json. |
| Model privacy/diagnostics | Synthetic native HTTP CLI verifies metadata before text, one rejected case/eight NOT TESTED, fixed education field path/no rejected-marker echo. Actual root cloud-tag check without a server correctly refuses it/9 NOT TESTED/exit2. JSON schema equality before/after diagnostic refinement verified. Not real model quality. |
| Delivery boundaries | Dependencies/locks/original30/35/38 manifests/nine-case review unchanged. Private-value/page-form exclusion checks passed during delivery; whole-shift private-value/file/author/frozen-data audit PASSED; verify remote after the documentation commit. |

The first scratch live-check invocation lacked the app import path; rerunning its script via stdin from apps/api fixed that invocation. The actual live check passed; this was not an application defect. No unresolved application test failure.

## Actual model and dataset limits

- Real Mac qwen2.5:3b: **1/9 schema/grounding-valid, minimum recall 0.1, empty-case accuracy 0.0; 8 failures**. Preserve this failed evidence.
- Real first qwen2.5:7b fast check: **term_not_in_quote, 0/1 valid; 8 NOT TESTED**. Prompt fix 3c0afba pushed; revised-prompt result still awaited. Download/OK reply is not requirements quality.
- Bare ollama opened glm-5.3-flash:cloud. Advised /bye then explicit downloaded local Qwen. Do not infer any owner data was sent; no such evidence.
- Latest set: **40 excerpts/seven employer labels, all Greenhouse**. 12 known deadlines, 3 exact start days from one Marshall Wace template, 33 role YES/NO labels. Literal In-Office/Hybrid headers do not prove geographic extraction. Automatic sponsorship abstains: 4 YES/14 NO labels, zero known-policy accuracy; zero false YES is not semantic policy assessment.
- New Cloudflare source probe failed 2/2 initially; initial report/labels retained. Intern YES annotation was incorrect against the existing internship-Unverified rubric and corrected after source-failure/code inspection. These are consumed regressions, not fresh held-out role acceptance. See REVIEW_NOV21.md/provenance-nov21.json.
- Nine-case model review measures minimum named-term/empty/company-background controls, not exhaustive education/experience semantics or precision. No real model exists in cloud; synthetic fixtures never accept Phase 2.

## Remaining Phase 2 work / owner input

1. **Need from owner next:** final revised-prompt local Qwen check result, not credentials. Fix the actual reason/path; do not relax grounding, cherry-pick cases or recommend another large download without evidence.
2. Independent multi-ATS/positive-date evidence at agreed ≥90% deadline/location/graduate/start-date targets; zero false confirmations. Same-ATS regressions/live repeats are insufficient.
3. Live non-Greenhouse adapters and actual full official-register compatibility/provenance remain unverified. Network settings must stay unchanged. Owner-side permitted checks/saved public postings are alternatives when available; no proxy/policy bypass or repeated draft request.
4. Adzuna and Find a Job are **not implemented**. Current public contracts/terms must be verified; Reed is the initial aggregator. Do not invent an API or call truncated snippets full vacancy text.
5. Existing duplicate histories still need supervised review; current source links preserve them. Manual weight tuning is delivered; automatic learning is not. No Phase 3 progression from a nine-case pass alone.

## Resume / coffee-sized next step

Read AGENTS.md and its context/spec/status, then inspect Git state. On the owner's Mac, from application-tracker:

```sh
git pull --ff-only origin dev/phase-1
LLM_PROVIDER=ollama LLM_MODEL=qwen2.5:7b python3 scripts/dev.py --check-model
```

Keep Ollama open. If needed, separately run `ollama run qwen2.5:7b "Reply with OK"` first. Do not open bare ollama's cloud chat. Paste only the final result. The one-command selectors do not edit private .env; selecting 7B for normal app use needs updating its existing private entries as SETUP.md describes, preserving all other settings. No new download/OAuth consent required if the model is already installed.

For the tracker: Control+C, pull, `python3 scripts/dev.py --migrate`, open **http://127.0.0.1:3000**. Later starts: `python3 scripts/dev.py`. No new project dependencies. All applications/private OAuth/Sheet data remain on the owner's Mac.

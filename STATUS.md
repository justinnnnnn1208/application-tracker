# Current project status

Reviewed: 21 November 2026, 04:15 Europe/London.

**Phase 2: roughly 90% implementation; acceptance incomplete.** This estimate is not a completion certificate or time forecast. Phase 1 was accepted for progression with the deferrals below. Phase 3 is not authorised. Sheets stays read-only; no managed network settings/publication changes.

## Current delivery

| Capability | Behaviour and evidence |
|---|---|
| Local tracker | Direct charcoal dashboard, jobs/deadlines/listing links, imported statuses, profile/CV fact review, worker and opt-in tab-open reminders. Owner confirmed 20 development-copy rows. Column E Notes repairs missing literal fields locally; owner edits/events/raw Sheet values survive. |
| Discovery | Greenhouse, Lever global/EU, Ashby, SmartRecruiters and private-key Reed search. First 20 details for SmartRecruiters/Reed; full bounded board for other ATS. Manual, not scheduled. Pending requests reuse tasks. Greenhouse has live checks; other adapters have synthetic contract/worker/browser tests, live compatibility unverified. |
| Identity and review | Canonical URL/official provider-board-ID aliases retain one application. Global/EU isolated; fuzzy titles are hints. Owner can link a new reviewed secondary listing; intake preserves content/Notes/events. Refuse another job's identity or distinct known same-board IDs/regions. Only manual secondary links removable, with pending-import/evidence guards. No existing-job history merge/delete. |
| Matching | Six deterministic explained criteria, reviewed-fact citations, active-job batch scoring/current ranking, Good/Poor feedback and manual keywords/weights. Known immigration/visa terms excluded from technology overlap. Source/fact/preference changes invalidate scores. Preference heuristic, not legal eligibility/proficiency/success probability. |
| Local requirements | Explicit per-job source-only native Ollama task, schema/quote grounding, bounded context/output/retries and stale/concurrent-source protection. Notes/profile/facts/CV/legal inputs excluded. Current terms feed deterministic overlap; otherwise labelled finite-keyword fallback. No real quality pass. |
| Local-model guard | Both local paths enforce loopback/no shell proxy/no redirects; before source text inspect `/api/show` with model name only. Refuse cloud tags, advertised remote aliases and missing/malformed metadata. Explicit hosted provider unchanged; no hosted fallback. Official Ollama source contract reviewed; tests include real synthetic loopback HTTP. |
| Sponsorship and register | Default Unverified. Owner-reviewed role quote/source/current context required for a manual finding; changed inputs invalidate it. Provenance is not semantic policy judgement. Dated official-asset CSV upload/exact name lookup remains a separate signal, never a score or role confirmation. Actual full official register verification pending. |
| Backups and updates | Backup-verifying `scripts/dev.py --migrate`, schema guard, restore to new destination, corrupt/unsupported archive guards, URI-safe exact SQLite filenames. Migration head eb81a592c387; score preference-v5-immigration-neutral-terms. No new dependencies/private configuration changes. |

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


## This night's checked changes

- Safe model setup/validation reasons; default root check makes one response attempt per case and stops first failure. Skipped cases stay NOT TESTED/null metrics; explicit --check-model-full retains retries/all cases. App extraction keeps initial attempt plus at most two validation retries.
- Tightened instructions/schema descriptions to the unchanged literal value-in-own-quote contract after the real 7B failure. No grounding relaxation or rejected-value feedback.
- Source review UI/API: 350 tests, typecheck/production build, full disposable production browser and 38-page regression passed at d66e0e6. Link → repeat intake → unlink retains one application/history.
- Model locality: 14 regressions failed before the fix and pass afterwards; full 364 API tests, browser and 38-page regression passed at 134f2ed. Actual root cloud-tag invocation with no server correctly refused it: 9 NOT TESTED, exit 2; no semantic pass.
- Fresh Cloudflare pages reproduced 2/2 strict URL failures. Accepting equal official posting identities fixes legacy/current metadata variants while distinct boards/IDs/regions/lookalike domains remain rejected. Final full **374 API tests** and production browser passed, including the genuine-page worker preservation test. Latest 40-page combined field/role regression passes; acceptance remains false.
- Earlier clean tracked-file export 2857020 passed fresh pinned installs, 303 tests/build/browser and actual init → backup-verifying migrate → local dashboard/proxy/auth → clean Control+C. Later code has incremental checks above. This is Linux release verification, not the outstanding Mac operational restore/notification test.

## Real-page and model evidence

Original 30/35/38 manifests and historical failures stay frozen. Latest **manifest-nov21.json: 40 genuine excerpts/seven employer labels, all Greenhouse**. Current combined field/role regression has zero extraction failures/false YES and matches basic labels. Only **12 known deadlines, 3 exact start days (same Marshall Wace template), 33 role-level YES/NO labels**. Null matches and literal In-Office/Hybrid headers do not prove positive dates or geographic extraction. Automatic sponsorship abstains: 4 YES/14 NO labels, zero known-policy accuracy; zero false YES is not evidence-assessment quality. phase_2_accepted=false.

Two new Cloudflare pages initially failed source extraction; preserve reports/nov21-initial-heldout.json. An incorrect internship YES annotation was corrected to the established Unverified rubric after the source failure/code inspection; original labels retained, corrected reviewed-nov21.json/provenance/review explain it. These are consumed regressions, not fresh held-out role acceptance. Databricks/Samsara redirects were refused; no extra hosts or substitute proxies.

Separate local-model review still has nine hash-bound minimum-term/empty/company-background cases, not exhaustive education/experience semantics or precision. Actual Mac qwen2.5:3b result: **1/9 schema/grounding-valid, recall 0.1, empty-case accuracy 0.0, eight failed**. Actual first qwen2.5:7b fast run: **term_not_in_quote, 0/1 valid, eight NOT TESTED**. Prompt fix pushed as 3c0afba; revised real result awaited. The 4.7 GB download/OK reply does not verify extraction quality. Bare ollama opened glm-5.3-flash:cloud; select downloaded Qwen explicitly. Cloud has no real Ollama server/weights; synthetic fixtures are not model quality.

## Remaining Phase 2 work

1. Obtain/review the revised-prompt local 7B result and fix actual failures without relaxing grounding or cherry-picking cases.
2. Independent multi-ATS/positive-date evaluation at agreed ≥90% deadline/location/graduate/start-date targets; zero false confirmations. Current same-ATS regressions are insufficient.
3. Live non-Greenhouse adapter and full official register compatibility/provenance checks. **Owner declined changing network settings on 21 November**; do not repeat that request or mutate/publish a draft unless they revisit it. Private Mac/API credentials are unavailable here.
4. Adzuna and Find a Job are not implemented. Verify permitted current public contracts/terms first; Reed is the initial aggregator. Do not invent endpoints or treat truncated adverts as complete vacancy text.
5. Supervised handling of conflicting pre-existing duplicate histories; current aliases/review avoid destructive merges. Manual weight tuning is delivered; automatic learning is not.

## Owner next step

From the Mac project root (no secrets in chat):

```sh
git pull --ff-only origin dev/phase-1
LLM_PROVIDER=ollama LLM_MODEL=qwen2.5:7b python3 scripts/dev.py --check-model
```

Paste the final check result. If bare Ollama opens a cloud chat, use /bye then `ollama run qwen2.5:7b "Reply with OK"` separately. These one-command model selectors do not change the app's private .env. If verified and selected for normal app use, update the existing private LLM_PROVIDER/LLM_MODEL entries as SETUP.md describes; preserve all other settings.

For the tracker, stop with Control+C, pull, then `python3 scripts/dev.py --migrate`; open http://127.0.0.1:3000. Later starts use `python3 scripts/dev.py`. No new dependencies, OAuth consent or Sheet write permission are needed for this delivery.

# Latest session handover

Reviewed: 9 November 2026 (Europe/London).

## Latest request and session scope

The owner asked to build persistent repository context after discussing a friend's project-memory approach. This session updates documentation, startup reading instructions and a repeatable handover structure. It does **not** resume the paused UI redesign, implement new app features, install plugins or start Phase 2.

Read [AGENTS.md](../AGENTS.md), [stable project context](context/PROJECT.md), [SPEC.md](SPEC.md), [STATUS.md](../STATUS.md) and this file before changes. [SETUP.md](SETUP.md) covers the Mac launcher, checks and exact read-only Google OAuth setup. [CLAUDE.md](../CLAUDE.md) routes Claude Code to the same shared instructions; it does not create another source of rules.

## Published baseline and local worktree

- Repository branch: `dev/phase-1`.
- Last published **application** commit: `1c7c8e29cdaf674290c71825c88493449ef91049` (direct dashboard, server-only API credential, no lock page/buttons).
- This session delivers documentation only. Later documentation commits are not evidence of a newer application build.
- Three pre-existing local UI redesign files are unfinished and deliberately excluded from this documentation delivery:
  - `apps/web/src/app/layout.tsx` — title/branding changes.
  - `apps/web/src/components/tracker.tsx` — dashboard/sidebar layout, job filters/sorting and disclosure changes.
  - `apps/web/src/components/workflows.tsx` — compact URL intake, setup sidebar and collapsible settings/tasks.
- The CSS still needs redesign work. The reference-inspired UI has not passed build/browser checks and is not published. Do not reset, overwrite, stage or silently ship these edits with an unrelated task.
- These UI edits may exist only in the retained cloud worktree. A fresh Git clone may not include them. Inspect Git state rather than assuming either version is present. The reference image was supplied in conversation; no `docs/design/dashboard.png` is saved in the repository.

## What changed in this session

- AGENTS.md now specifies the session-start reading order and status/handover update routine. Stale worker/evaluation command notes were corrected from the actual source.
- Stable project/owner working preferences live in `docs/context/PROJECT.md`.
- STATUS.md distinguishes published evidence from untested local UI edits, and records all six Phase 1 criteria with their limits.
- This handover and `docs/templates/SESSION_HANDOVER.md` provide a repeatable stop/resume record.
- README points to the shared context and accurate current implementation summary.
- SETUP.md records Mac run commands, read-only Google Cloud setup and private credentials-file location. No Google credentials were requested in chat or created by this task.

## Phase 1 acceptance state

| Criterion | Status | Evidence and limits |
|---|---|---|
| Ten pasted URLs create correct job rows | PASSED — fixtures | Prior API/task/worker/extractor/DB test using ten synthetic job pages; live portals not tested |
| Re-pasting creates no duplicates | PASSED — fixtures | Same test requeues tracking-URL variants; stable IDs/count/history checked |
| Sheet import preserves all rows | NOT TESTED on development copy | Synthetic fixture preservation test passed; actual copy not configured/verified |
| Status write touches only its target cell, preserving formulas/formatting/notes | NOT TESTED | Writes disabled pending read-only import verification and separate approval |
| Database and storage backup restores | PASSED — disposable data | Prior content/checksum/integrity/tamper tests; owner laptop restore not verified |
| Sponsorship defaults to UNVERIFIED | PASSED | Prior API/DB/extraction tests; no automatic confirmed sponsorship implemented |

Phase 1 remains incomplete, with a rough progress indicator of about 60%. The owner must explicitly confirm it is verified before Phase 2 starts. A rough percentage or an old passing fixture suite does not satisfy that gate.

## Verification record

Previously recorded for the published application baseline, not rerun by this documentation task:

- API/service suite: 42 passed, one dependency deprecation warning.
- TypeScript and production build: passed.
- Desktop/mobile production browser smoke: passed for direct dashboard/reload/reopen/server restart, credential/origin guards, manual jobs/history, profile/facts and deadlines.

These results do not cover the three paused UI files above, live Google import, real portals, a real-page extraction evaluation set or all expanded UI workflows. No phase-completion claim is made.

Documentation delivery checks passed: nine documents were checked and 51 local links/references resolved; entry-point routing and evidence markers were checked; `git diff --check` passed; the three pre-existing UI file fingerprints were unchanged; staged paths contained documentation only, with no local credential values. Application tests were not rerun for Markdown-only changes.

## Owner inputs and permissions still needed

- Development-copy spreadsheet ID, exact tab name and header-row number. Header names were already provided and are documented in SETUP.md; do not request them again.
- Owner completes Google Cloud Web OAuth setup and puts the downloaded JSON in the ignored local location described in SETUP.md. Never request the JSON, client secret, token or encryption key in chat.
- Extraction provider/model choice before enabling hosted fallback; separate approval before sending personal data to any hosted provider.
- Phase 2 is **not authorised to begin** until the owner confirms Phase 1 is verified. Sheet writes, touching the original tracker, real application-portal runs and auto-submit remain blocked by the stated owner/agent rules.

None of these owner inputs blocks the documentation/context task itself.

## Resume in this order

1. Read the entry-point/context/spec/status/handover files and inspect the actual branch/worktree.
2. Confirm the owner's current requested task. Context setup is complete once checked/pushed; do not silently resume the paused UI work.
3. If the owner resumes UI work: preserve/inspect the three local edits, complete Inter/blue styling and responsive/accessibility behaviour from SPEC.md section 13, adapt smoke selectors to the new headings, then run build/type/browser checks using disposable data. Keep later-phase elements hidden.
4. For Google work: use SETUP.md, verify configuration **names/presence only**, connect only the development copy with readonly scope, and compare the actual read-only import with that copy. Keep writes disabled.
5. Update STATUS.md and this handover with actual results, stage only the completed task, push to `dev/phase-1`, verify the remote commit and give the owner pull/restart instructions.

## Delivery record

- Shared-context documentation was pushed in commit [`e80d9c9`](https://github.com/justinnnnnn1208/application-tracker/commit/e80d9c9060d4ec7941e8fc16a8ac8f476089631a). Its full SHA matched the GitHub `dev/phase-1` ref in a read-only remote verification.
- This final handover record and one-at-a-time setup clarification are a documentation-only follow-up. Use Git history for the newest documentation commit; the application baseline remains `1c7c8e2`.
- All three runtime UI edits listed above remain local and excluded from this delivery. They were not modified by the context task.
- Owner next step, from the local repository: `git pull --ff-only origin dev/phase-1`. No app restart is needed for documentation changes. If local changes conflict, preserve them and investigate rather than forcing the update.
- No owner input is required to complete context setup. Google configuration inputs listed above are for later integration work.

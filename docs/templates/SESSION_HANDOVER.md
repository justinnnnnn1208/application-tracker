# Session handover template

Copy this structure into `docs/HANDOVER.md` when work stops. Replace placeholders; this template is not evidence of completed work. Use PASSED, FAILED or NOT TESTED, and state whether evidence comes from fixtures, a disposable database, a local browser or a live development-copy integration.

## Session

- Reviewed date/time and timezone:
- Owner's latest request and authorised scope:
- Branch and last published application commit:
- Current phase and any explicit progression gate:
- Worktree state, including pre-existing/unrelated edits:

## What changed

| Work | State: planned/implemented/tested/blocked/complete | Files or commit | Evidence/limits |
|---|---|---|---|
| Fill in actual work | NOT TESTED until verified | Add paths | Do not infer a pass |

## Phase 1 acceptance

| Criterion | Result | Command/test, outcome and environment | Remaining limit |
|---|---|---|---|
| Ten pasted URLs create correct job rows | NOT TESTED | Fill in evidence | Include fixture/live distinction |
| Re-pasting creates no duplicates | NOT TESTED | Fill in evidence | Include workflow tested |
| Sheet import preserves all rows | NOT TESTED | Fill in evidence | Development copy only |
| Status write changes only the target cell, preserving formulas/formatting/notes | NOT TESTED | Fill in evidence | Writes remain blocked until approved |
| Database and storage backup restores successfully | NOT TESTED | Fill in evidence | Restore into a new destination |
| Every job defaults to UNVERIFIED unless supported by evidence | NOT TESTED | Fill in evidence | A sponsor licence is not role evidence |

## Checks performed this session

| Command/check | Working directory | Exit code/count/result | What it verifies |
|---|---|---|---|
| Fill in only checks actually run | Add directory | Add actual outcome | Do not copy an old pass as a new run |

## Unfinished work and blockers

- Exact unfinished paths and their purpose; say whether changes are committed or only local.
- Known failures, missing credentials/configuration, unverified assumptions and unavailable evidence.
- Owner decisions or values needed, with secure entry location. Never include secret values, CV text or legal answers.
- Explicitly unauthorised actions and progression gates still in effect.

## Resume in this order

1. Read AGENTS.md and its linked context files, then inspect current Git state.
2. Identify the smallest next authorised action and preserve existing work.
3. Complete and verify the affected workflow; use relevant tests and record results.
4. Update status/handover, commit and push only the completed scope, and verify the remote commit.

## Delivery and owner next step

- Published branch/commit and remote verification result, or why work was not pushed:
- Uncommitted work deliberately excluded:
- Exact owner pull/run command, if needed:
- Owner input needed next, or explicitly none:

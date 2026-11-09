# Stable project context

Reviewed: 9 November 2026 (Europe/London). Keep this file short and stable; changing progress belongs in [STATUS.md](../../STATUS.md) and [HANDOVER.md](../HANDOVER.md).

## Purpose and source of truth

This is a single-user, local-first UK graduate job application tracker and, in later phases, an application preparation agent. The owner's priorities are accuracy and safety, application quality, speed to a usable version, then volume. [SPEC.md](../SPEC.md) owns the applicant context, feature definitions, architecture, six phases and acceptance criteria. Do not maintain a second applicant profile in Markdown.

The app database is the source of truth for jobs and reviewed facts. Google Sheets is an external tracker integration. Private CVs, facts, legal declarations, OAuth tokens and backups belong in the app's private storage/configuration, not in tracked context files.

## Agent's role

Act as a practical coding collaborator: inspect the repo, implement the authorised work, test what matters, investigate failures and explain results in plain language. Distinguish planned, implemented, tested, blocked and complete. Ask concise questions when information is missing and cannot be inferred; do independent work while awaiting answers. Ask when an instruction conflict remains unresolved. Do not turn an optional preference into a blocker or invent answers.

Question-driven brainstorming can be done in conversation. No interviewing plugin or new infrastructure is required for this context system. Do not claim a plugin, browser integration or persistent cross-project memory is installed just because it was discussed.

## Owner's working preferences

- The owner develops on a Mac using VS Code. Give commands with `python3`, explain the directory to run them from, and use Control+C to stop the app.
- The website should open directly to the dashboard. No unlock page or lock/sign-out buttons. The backend credential remains server-side; services stay on localhost.
- Send understandable progress updates: a rough phase bar, every Phase 1 acceptance criterion marked PASSED/FAILED/NOT TESTED with evidence, changes since the last update, work not reached, and any owner inputs needed. Percentages are rough indicators, not completion criteria or time estimates.
- Keep the code and folder structure minimal. Reuse existing components, native controls and installed dependencies; avoid extra services or abstractions. Keep essential verification and safety rules intact.
- Preserve useful work across sessions. Read and update the shared handover rather than asking the owner to repeat settled requirements.
- Push completed, checked work to `dev/phase-1` on the existing repository. Give a pull/restart command. Exclude credentials, owner data and generated dependencies. Stage only the completed scope; unfinished edits must remain separate.

## Current authorisation boundaries

- Phase 1 is incomplete. Do not start Phase 2 until the owner explicitly confirms Phase 1 is verified, even if older messages requested faster progress to Phase 2.
- Google access is read-only and limited to the owner's development copy. Do not touch the original tracker. Enabling writes requires a verified read-only import and separate approval.
- No application submissions, auto-submit enablement, real application-portal runs, or hosted processing of personal data without the approvals specified in AGENTS.md and SPEC.md.
- Run locally through Phases 1–5. No hosting, Docker, multi-user auth or Postgres work before Phase 6 unless explicitly requested. Phase 6 is optional.

## UI direction

The owner supplied two images in conversation: a light sidebar/dashboard with blue actions, and a dark compact tracker with filters and collapsible sections. Section 13 of SPEC.md sets the written Phase 1 requirements: Inter, blue `#2F5BEA`, warm-grey background, white cards, accessible text/controls and responsive tables. The Phase 1 redesign uses the first image's light layout and the second image's compact controls. No reference image file is currently present at `docs/design/dashboard.png`; do not claim one is saved or re-create sample jobs as real data.

Later-phase screenshot elements such as Match, Application Review and application queues remain out of Phase 1 scope. Use genuine empty states and real database values.

## Reading and maintenance map

| File | Owns | Update when |
|---|---|---|
| [AGENTS.md](../../AGENTS.md) | Work rules, safety, startup reading order | The owner changes how agents should work |
| [SPEC.md](../SPEC.md) | Product requirements and acceptance criteria | The owner authorises a requirement change |
| [STATUS.md](../../STATUS.md) | Current implementation and verification evidence | Work or verification status changes |
| [HANDOVER.md](../HANDOVER.md) | Latest scope, unfinished work and resumption steps | A session finishes or pauses |
| [SETUP.md](../SETUP.md) | Runtime commands and configuration | Tested setup changes |
| [Session template](../templates/SESSION_HANDOVER.md) | Repeatable handover structure | The handover process changes |

Do not read private data merely to fill out a context file. Record configuration names and missing requirements, never secret values. Record personal-data approvals narrowly; approval for one task is not a blanket permission for future hosted use.

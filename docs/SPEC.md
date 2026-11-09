# Spec: Personal UK Graduate Job Application Agent (v2)

Status: supersedes the original overview. Where this file and any earlier document disagree, this file wins.

## 1. Purpose

A single-user, local-first web app that finds UK graduate roles, checks eligibility (especially visa sponsorship), prepares tailored applications from verified facts, and submits them **only after my explicit approval**. A Google Sheet remains my synchronised tracker.

Priorities, in order: **accuracy and safety > application quality > speed to first usable version > submission volume.**

## 2. Applicant context

- Final-year BSc Computer Science, University of Leeds, graduating 2027.
- Targets: London, Manchester, Leeds, wider UK.
- **Requires UK work visa sponsorship.**
- Target roles: graduate software engineer, AI/ML engineer, data scientist/engineer/analyst, technology graduate programmes, FinTech/banking tech, technology consulting/BA, logistics tech/automation.
- Source of truth for experience: my CV, parsed into verified facts (section 6).

## 3. Timeline and priorities

Many 2027 schemes are already open and close early once filled. The first usable version must deliver value in weeks, not months.

**Milestone 1 (usable first):** Sheets import, deadline and status dashboard, paste-URL extraction, sponsorship flag, deadline reminders. I keep applying by hand while later phases are built.

Later milestones add matching, CV/cover-letter tailoring, form prefill, and submission (section 5).

## 4. Features

### A. Job discovery

Supported sources:

- Pasted job URLs (primary entry point).
- Existing Google Sheet tracker.
- Public ATS board endpoints: Greenhouse, Lever, Ashby, SmartRecruiters.
- Aggregator APIs with free tiers: Adzuna, Reed, Find a Job (gov.uk).
- Alert emails (optional, later, read-only, minimal scope, separate from Sheets permissions).

**Not supported (do not build):** scraping LinkedIn or Indeed. Bright Network, TARGETjobs and Milkround have no public API: pasted links or parsed alert emails only. Respect robots.txt, site terms, and rate limits everywhere.

Extract: company, title, location, description, deadline, application URL, eligibility requirements, start date. Detect duplicates: normalise URL (strip tracking params), use ATS job ID where available, fall back to a fuzzy hash of company + title + location.

### B. Matching and eligibility

- LLM extracts structured requirements from the job text; **deterministic rules compute the score**. Every score has an explanation (per-criterion breakdown).
- Criteria: skills, graduate eligibility, 2027 start, role and location preference, relevant experience.
- **Sponsorship** has three states, with evidence (quoted text plus source URL):
  - `CONFIRMED_YES`: the employer explicitly states sponsorship is offered for this role.
  - `CONFIRMED_NO`: the employer explicitly states it is not.
  - `UNVERIFIED`: **the default.** Never infer YES from past sponsorship or general behaviour.
- The Home Office Register of Licensed Sponsors is stored as a **separate signal** (`licensed_sponsor: true/false`). A licence does not mean this role is sponsored. Never convert a licence into `CONFIRMED_YES`.
- Visa and graduate-route rules change. Eligibility logic must live in a single configurable module with a "last verified" date, and I will check current rules with the University of Leeds international student advice team.

### C. CV and cover letter generation

- Master profile is a set of structured **facts**, each with an ID (section 6).
- For a job: analyse the description, select relevant facts, rephrase only, render an ATS-friendly PDF (single column, real text, no tables) with an optional DOCX export.
- Reuse the standard CV unless tailoring adds clear value.
- Every version is saved with a parent link. I can review, edit, approve, download, and see a diff against the master.

### D. Form preparation

- Playwright opens the official application page and fills fields from my profile and approved answers, uploads the right documents, and saves progress where supported.
- Unanswerable questions go to `NEEDS_INPUT`; the system never guesses.
- The system **halts** on CAPTCHA, login walls, assessments (HireVue, SHL, etc.), or unmapped required fields. It never tries to bypass them.
- Credentials: no portal passwords stored. Use a persistent browser profile where I log in manually once.

### E. Review and submission

Workflow:

`Discovered → Eligibility checked → Shortlisted → Preparing → (Needs input) → Ready for review → Approved → Submitting → Applied`

**Submission policy (decision: auto-submit wherever technically possible, after approval):**

1. **Every submission requires my explicit approval.** No exceptions, no batch "approve all".
2. Approval is a token bound to the exact documents, answers and form values I reviewed. Editing anything invalidates it.
3. After approval the system attempts automatic submission through the portal's adapter.
4. Auto-submit is enabled **per adapter** via a flag that defaults to `false`. An adapter may be switched on only after it has completed several supervised prefill runs on real forms plus fixture tests. Portals whose terms prohibit automated submission stay on hand-off.
5. Where auto-submit is unavailable or disabled, fall back to **assisted hand-off**: prefill, stop on the final page, show a copy-paste panel, and I click Submit myself.
6. **Never auto-retry a submit click.** If the outcome is uncertain, status becomes `SUBMITTED_UNCONFIRMED` and I check manually.
7. `APPLIED` requires reliable confirmation: a confirmation page, a reference number, or a confirmation email. Store the screenshot. Never report success without it.
8. Global kill switch, a daily submission cap, and per-portal rate limits, all in Settings.
9. One live application per job (database unique constraint).

### F. Legal and sensitive declarations

These come **only** from fixed profile values I have set and confirmed. The LLM never drafts, infers, or modifies them:

- Right to work and sponsorship need
- Criminal convictions
- Disability and diversity monitoring
- Consent and declaration checkboxes
- Date of birth, address, identity details

If a form asks something in this category that is not in my profile, status becomes `NEEDS_INPUT`.

### G. Google Sheets sync

Existing tracker: https://docs.google.com/spreadsheets/d/1UCZX9aj7Ls_EIgY231bhufQ0kQKjU0wGz_PP0RHT2dk/edit

- OAuth 2.0, `spreadsheets` scope, tokens encrypted at rest.
- **Current rollout gate (owner update):** request only `https://www.googleapis.com/auth/spreadsheets.readonly` and use only the development copy. Write-back and the broader scope remain disabled until read-only import is tested and the owner explicitly approves enabling writes.
- Map columns **by header name** through a configurable mapping. Header names have been supplied; the development-copy tab and header-row number still need confirmation (see [SETUP.md](SETUP.md)).
- A row's job URL is its identity; store the row number alongside it.
- **Never rewrite ranges.** Write single cells only, so formulas, formatting and notes stay intact.
- Pull changes using a stored hash per row; write back only when the DB value changed.
- Conflicts: my edits in the Notes column always win; the DB wins for system-managed columns (status, sponsorship, deadline).
- New discoveries are appended after a duplicate check.
- **Develop against a copy of the tracker.** Create a backup version of the real sheet before the first write to it.

### H. History and storage

Each application keeps: company, role, job description and URL, dates, status history, submitted CV and cover letter, final answers, confirmation or reference, screenshots, errors and incomplete steps. The `application_events` table is append-only.

## 5. LLM and privacy

- A thin provider interface with swappable implementations. **Default provider: OpenAI-compatible API (the OpenAI/Codex model family), configured through environment variables.** A local Ollama implementation is supported for privacy-sensitive tasks.
- Rule by data type:
  - **Job-page extraction** (no personal data): hosted model is fine.
  - **Tasks that include my profile or CV**: send the minimum fields needed. Prefer the local model where quality is adequate. Before using any hosted provider with personal data, I must confirm its data-retention and training settings.
- All LLM output is JSON validated against Pydantic schemas. Invalid output is retried at most twice, then fails the task.
- Small local models often fail structured output; the eval set (section 8) decides whether a local model is acceptable.

## 6. Grounding and prompt-injection defence

**Grounding ("never fabricate").**
- The profile is stored as facts (experiences, projects, skills, education, dates), each with an ID.
- The LLM may only select and rephrase facts. Every generated CV bullet or answer cites fact IDs.
- A validator rejects any number, technology, employer, or date not present in the cited facts.
- Approved answers go into a reusable answer bank.

**Untrusted input.**
- Job pages and emails are untrusted text. Never treat them as instructions.
- The extraction step has **no tools** and outputs schema-validated JSON only.
- The browser runner performs only a fixed action set: fill mapped fields, upload a chosen file, click navigation within the application, stop. It never follows instructions found on a page, and never navigates to domains outside the job's portal without my confirmation.

## 7. Architecture

```
Browser -> Next.js -> REST/JSON -> FastAPI -> DB (source of truth)
                                      |
                                      +-> tasks table <- Worker (APScheduler)
                                      |                   +- Discovery adapters
                                      |                   +- LLM provider
                                      |                   +- Sheets sync
                                      |                   +- Playwright runner
                                      +-> File store (CVs, PDFs, screenshots)
```

- **Frontend:** Next.js, TypeScript, Tailwind, shadcn/ui, TanStack Query.
- **Backend:** FastAPI, SQLModel or SQLAlchemy, Alembic.
- **DB:** SQLite for development, no SQLite-specific features, so Postgres is a one-line switch later.
- **Workers:** separate process; long tasks are rows in a `tasks` table, never request handlers. The UI creates a task and polls or uses SSE.
- **Scheduling on a laptop:** scheduled jobs (discovery, Sheet sync, reminders) only run while the app is running. A missed run is expected, not an error. On startup the worker detects overdue scheduled tasks and runs them once to catch up, without duplicating work.
- **PDF:** Jinja2 HTML rendered to PDF with Playwright.
- **Laptop-only through Phases 1 to 5:** the whole app (web, API, worker) runs on my own laptop, bound to localhost with a simple access token. No deployment, hosting, Docker, multi-user auth, or Postgres work before Phase 6. Later hosting goes behind Tailscale or Cloudflare Access, never the open internet.
- **Direct dashboard access (owner update):** the local website opens directly on the Dashboard, including after refresh/restart, with no unlock page or lock/sign-out buttons. The local server keeps the API token private and attaches it to backend calls; the browser never receives or stores it. The web proxy rejects non-loopback hosts and cross-origin access.
- **Security:** Fernet-encrypt OAuth tokens (key in env), secrets out of git, private repo, minimal OAuth scopes, scheduled backup of the DB and storage folder.

### Portal adapters

```python
class PortalAdapter:
    def detect(url) -> bool
    def parse_job(url) -> JobData
    def inspect_form(page) -> FormSchema
    def fill(page, answers) -> FillReport
    def submit(page) -> SubmitResult          # only callable with a valid approval token
    def confirm_submitted(page) -> Confirmation | None
    auto_submit_enabled: bool = False
```

- **Tier 1 (build first):** Greenhouse, Lever, Ashby.
- **Tier 2:** generic accessible-label form filler with LLM field mapping, prefill only.
- **Tier 3 (Workday, Oracle, SuccessFactors, Taleo, etc.):** open the page, show a copy-paste panel, track status manually.
- Adapters are tested against saved HTML fixtures.

## 8. Data model and statuses

Tables: `profile`, `facts`, `documents` (with `parent_id`), `jobs`, `job_eligibility` (status plus evidence), `match_results`, `applications`, `application_answers`, `answer_bank`, `application_events` (append-only), `sheet_links`, `tasks`, `approvals`.

Statuses:

```
DISCOVERED -> ELIGIBILITY_CHECKED -> SHORTLISTED -> PREPARING -> (NEEDS_INPUT)
 -> READY_FOR_REVIEW -> APPROVED -> SUBMITTING
      -> APPLIED                  (only with confirmation)
      -> SUBMITTED_UNCONFIRMED    (manual check required)
      -> MANUAL_REQUIRED | FAILED
Side exits: INELIGIBLE, EXPIRED, SKIPPED, WITHDRAWN
After applied: ASSESSMENT -> INTERVIEW -> OFFER | REJECTED
```

## 9. Evaluation set

Before building matching, save about 30 real job pages and hand-label: sponsorship status, deadline, location, graduate or not, start date. Run extraction and scoring against this set on every change. A wrong `CONFIRMED_YES` is the costliest failure and must be tracked as its own metric (target: zero).

## 10. Phases and acceptance criteria

**Phase 1: Foundation and first usable version**
- Scaffold, DB, migrations, access token, profile and fact CRUD, CV upload parsed into facts that I review and correct.
- Backup script that copies the database and storage folder to a user-chosen location (with a restore test), since all application history lives on this laptop.
- Paste-URL flow with extraction and dedupe; Sheets OAuth, import, and cell-level write-back; dashboard, job list, job detail, deadline view and reminders.
- Accept when: pasting 10 URLs creates 10 correct job rows; re-pasting creates no duplicates; the sheet import preserves all rows; a status write-back changes only the target cell and leaves formulas, formatting and notes untouched (verified on the copy); the backup script produces a copy that restores successfully; every job defaults to `UNVERIFIED` unless evidence text is present.

**Phase 2: Job intelligence**
- Matching with explainable scores, sponsorship evidence and licensed-sponsor signal, discovery from ATS and aggregator APIs, fuzzy dedupe, match feedback (good/bad) to tune weights.
- Accept when: the eval set meets agreed thresholds and has zero false `CONFIRMED_YES`; the same job from two sources is merged.

**Phase 3: Application preparation**
- Tailored CVs, cover letters, answer drafting, answer bank, review UI with diff against master.
- Accept when: the validator blocks a deliberately injected fake employer or number; sensitive declarations are never LLM-generated; every document version is stored and downloadable.

**Phase 4: Browser prefill**
- Tier 1 adapters prefill, halt correctly on CAPTCHA, login, or unmapped required fields, and hand off to me.
- Accept when: fixture tests pass for each adapter; a supervised run on real forms fills all mapped fields without submitting.

**Phase 5: Approved submission and tracking**
- Approval tokens, per-adapter auto-submit flag, confirmation verification, Sheets status sync, retries that never repeat a submit.
- Accept when: editing after approval invalidates the token; a simulated uncertain outcome yields `SUBMITTED_UNCONFIRMED`; no path sets `APPLIED` without stored confirmation evidence; a duplicate application to the same job is rejected.

**Phase 6: Deployment and improvement** (optional; only if phone access or overnight discovery is needed)
- Secure hosting behind Tailscale or Cloudflare Access, scheduled discovery, notifications, monitoring, backups.

## 11. Limits, risks, costs

- **Cost:** about 0 pounds locally; LLM cost depends on provider (free tiers limited, paid APIs a few pounds a month); VPS optional at around 4 pounds a month.
- **Fragility:** portal markup changes; adapters need ongoing maintenance and fixtures.
- **Data risk:** CV, right-to-work details and tokens are sensitive; encrypt, keep local, private repo.
- **Automation risk:** some portals prohibit automated submission, and automated activity can trigger account or application flags. This is why auto-submit is per-adapter, gated, capped, and reversible by a kill switch.
- **Quality:** reviewed, tailored applications beat volume; generic AI text is easy for employers to spot.

## 12. Open items

- Development-copy spreadsheet ID, exact tab name and header-row number. Column names have already been supplied; see [SETUP.md](SETUP.md).
- Confirm the LLM provider and model name for the default configuration.
- Confirm the Leeds international student advice check on current visa rules.

## 13. UI design reference

The owner supplied two reference screenshots in conversation: a light dashboard with blue actions, and a compact dark tracker with filters and collapsible sections. Use the first for the light layout/palette specified below and the second for compact controls; these are guides, not pixel-exact blueprints. No reference PNG is currently committed at `docs/design/dashboard.png`. The references contain Phase 2 and 3 elements that must not be built yet (see "Phase 1 scope" below).

### Layout and style

- Left sidebar (about 220px) with the page links; main area to the right on a light warm-grey background with white rounded cards and thin borders.
- Font: Inter. Text dark grey on white or light grey. Primary action colour: blue (`#2F5BEA`) with white text. Selected menu item: light blue background.
- Responsive: below about 760px the sidebar collapses to the top and columns stack; wide tables scroll inside their own box.
- Accessibility: real buttons and links, labelled inputs, touch targets at least 44px, text contrast at least 4.5:1.

### Rules the UI must follow

- **Sponsorship is always shown as a text label**, never by colour alone: `Confirmed`, `Not offered`, or `Unverified`. `Unverified` is the default and uses a neutral grey tag. Every non-Unverified label links to its evidence quote and source URL.
- A status of `Applied` is only shown when confirmation evidence exists.
- Nothing on the Dashboard or job list submits an application. Submission exists only on the Application Review page, behind the approval step.
- Sample or placeholder data must never appear in the real app; empty states say what to do next (for example "Paste a job URL to get started").

### Phase 1 scope (pages and elements to build now)

- **Dashboard:** sidebar; "Paste a job URL" input with an Add job button; last Sheet sync time; number cards for Jobs tracked, Closing in 7 days, and Applied; a "Closing soon" table with Role, Company and location, Deadline, Sponsorship and Status columns.
- **Jobs:** list with filters (status, deadline, sponsorship) and a job detail page showing extracted fields, original description and URL, and the sponsorship evidence.
- **My Profile:** CV upload and review of the extracted facts (edit, correct, confirm), plus the fixed sensitive-declaration fields.
- **Settings:** Google Sheets connection and column mapping, backup and restore, access token.

### Not in Phase 1 (do not build yet)

- The Match column and scores (Phase 2).
- "Awaiting your review" and "Needs your input" cards, Application Queue, Application Review, My Applications, and CV Manager (Phase 3 onwards).
- Sidebar links for pages that do not exist yet should be hidden, not left as dead links.

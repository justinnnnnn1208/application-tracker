# Spec: Personal UK Graduate Job Application Agent (v2)

Status: supersedes the original overview. Where this file and any earlier document disagree, this file wins.

## 1. Purpose

A single-user, local-first web app that finds UK graduate roles, checks eligibility (especially visa sponsorship), prepares tailored applications from verified facts, and submits them **only after my explicit approval**. A Google Sheet remains my synchronised tracker.

Priorities, in order: **accuracy and safety > application quality > speed to first usable version > submission volume.**

## 2. Applicant context

- Final-year BSc Computer Science, University of Leeds, graduating 2027.
- Targets: London, Manchester, Leeds, wider UK.
- **Current owner update:** prioritise graduate/junior UK technology roles regardless of sponsorship availability. Sponsorship is informational and must not exclude or penalise a role. The owner mentioned the Graduate visa; do not infer eligibility, expiry dates or change fixed legal/right-to-work declarations without owner-confirmed profile values.
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
- **Current rollout (owner update):** the owner reported all 20 development-copy jobs imported and approved copy-only status write-back. Read-only remains the default. Only an explicit private `SHEETS_WRITE_COPY_ID` enables the broader `spreadsheets` scope, followed by renewed consent. The app restricts mutations to single mapped status cells on that copy; the original remains blocked. Live write verification is still pending. The owner subsequently explicitly accepted deferring live write verification and authorised Phase 2, with Mac notification and operational restore checks also outstanding. Keep Sheets read-only by default.
- Map columns **by header name** through a configurable mapping. The development-copy configuration, tab and header row were supplied, and the owner confirmed all 20 rows imported. Preserve the existing Mac configuration; do not ask for settled values again (see [SETUP.md](SETUP.md)).
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

**Phase 1 progression decision (9 November 2026):** the owner accepted progression with the live status-cell preservation test deferred and Mac notification/operational restore checks outstanding. These remain recorded limitations, not passed tests. The owner confirmed the delivered listing links and imported-status UI checks on their Mac.

**Phase 2: Job intelligence**
- Matching with explainable scores, informational sponsorship evidence and licensed-sponsor signal, discovery from ATS and aggregator APIs, fuzzy dedupe, match feedback (good/bad) to tune weights. Prioritise graduate/junior UK technology roles; do not exclude or penalise roles for sponsorship status. Matching awaits the real hand-labelled evaluation set; the owner agreed initial field-accuracy targets of at least 90% for deadline, location, graduate-role classification and start date, with zero false CONFIRMED_YES. Unknown-label coverage and held-out performance must be reported separately.
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

- Development-copy configuration and columns were supplied and the owner confirmed all 20 rows imported. Live single-cell write verification is deferred; do not ask for settled configuration again. See [SETUP.md](SETUP.md).
- Local Ollama was selected on 20 November 2026. The initial qwen2.5:3b failed real checks; qwen2.5:7b is the next candidate for the reported 16 GB Mac. Revised-prompt real quality still needs verification.
- Confirm the Leeds international student advice check on current visa rules.

## 13. UI design reference

The owner supplied two reference screenshots in conversation: a light dashboard with blue actions, and a compact dark tracker with filters and collapsible sections. Use the first for layout and the second for compact controls; the owner subsequently requested a charcoal-grey theme; these are guides, not pixel-exact blueprints. No reference PNG is currently committed at `docs/design/dashboard.png`. The references contain several phases: Phase 2 discovery/matching is now authorised; application preparation/review remains gated by later phases. The accepted Phase 1 baseline is described below.

### Layout and style

- Left sidebar (about 220px) with the page links; main area to the right on a charcoal-grey background with slightly lighter dark rounded cards and thin borders.
- Font: Inter. Text off-white with readable muted grey labels. Primary action colour: blue (`#2F5BEA`) with white text; links use lighter blue for contrast. Selected menu item: muted slate-blue background. Native form controls use the dark colour scheme.
- Responsive: below about 760px the sidebar collapses to the top and columns stack; wide tables scroll inside their own box.
- Accessibility: real buttons and links, labelled inputs, touch targets at least 44px, text contrast at least 4.5:1.

### Rules the UI must follow

- **Sponsorship is always shown as a text label**, never by colour alone: `Confirmed`, `Not offered`, or `Unverified`. `Unverified` is the default and uses a neutral grey tag. Every non-Unverified label links to its evidence quote and source URL.
- A status of `Applied` is only shown when confirmation evidence exists.
- Nothing on the Dashboard or job list submits an application. Submission exists only on the Application Review page, behind the approval step.
- Sample or placeholder data must never appear in the real app; empty states say what to do next (for example "Paste a job URL to get started").

Desktop deadline reminders (owner clarification): opt-in browser notifications, displayed through macOS when browser/OS settings allow them. While the tab is open, notify once per job per UK day for active deadlines within 7 days; exclude expired/applied source rows. No reminders run after the tab closes. Keep the deadline view available when permission is denied.

### Phase 1 scope (accepted baseline)

- **Dashboard:** sidebar; "Paste a job URL" input with an Add job button; last Sheet sync time; number cards for Jobs tracked, Closing in 7 days, and Applied; a "Closing soon" table with Role, Company and location, Deadline, Sponsorship and Status columns.
- **Jobs:** list with filters (status, deadline, sponsorship) and a job detail page showing extracted fields, original description and URL, and the sponsorship evidence.
- **My Profile:** CV upload and review of the extracted facts (edit, correct, confirm), plus the fixed sensitive-declaration fields.
- **Settings:** Google Sheets connection and column mapping, backup and restore, access token.

### Elements beyond Phase 1

- The Match column and scores belong to Phase 2, which the owner has now authorised.
- "Awaiting your review" and "Needs your input" cards, Application Queue, Application Review, My Applications, and CV Manager (Phase 3 onwards).
- Sidebar links for pages that do not exist yet should be hidden, not left as dead links.

### Current Phase 1 status presentation

Show original Sheet statuses in job rows and details. Applied source rows use “Applied — imported from Sheet” and have a dedicated filter. Dashboard shows the imported count separately in the Applied metric explanation; the app’s confirmed Applied count remains zero until confirmation evidence is supported. Direct Open listing links are available in the job table and details. No imported claim creates a confirmed APPLIED state.

### Phase 2 first matching delivery (17 November 2026)

Thirty genuine reviewed posting snapshots now exist in fixtures/eval, from four employers on Greenhouse. Public application forms/scripts are excluded; original visible posting content is retained with source/capture/hash provenance. The initial parser/classifier was developed using this set, so report results as development evidence, not held-out generalisation. There are no exact-day start-date positives; matching null values does not prove positive-date extraction.

Per-job matching runs locally in the task worker. It is an explained preference heuristic, not personal/legal eligibility or a probability of success. Default weights: role 20, graduate level 25, location 20, reviewed skill overlap 20, reviewed experience overlap 10 and start year 5. Existing configured weights/roles and profile locations/graduation year are used when present. Keyword overlap only uses reviewed facts and cites their IDs; it is not proof of proficiency. Source text never supplies applicant facts. Start-year comparison does not establish month/day availability.

Sponsorship is not included in score inputs or weights. Source sponsorship statements, Notes and licences do not become confirmed states. Confirmation/evidence assessment and licensing signals remain unfinished. Good/Poor feedback is stored against a current score, but no automatic weight tuning is delivered yet. Job/reviewed-fact/preference changes invalidate stored scores; stale scores must not be used for feedback until recalculated.

Imported rows require a real title plus available vacancy text or a clearly labelled Notes summary before scoring. Pasting an existing listing URL can fill missing title/company/location/description/requirements/dates, while preserving already populated owner content, Notes, tracker history, app status and identity. Repeated imports stay deduplicated. Non-Greenhouse source support remains subject to the existing host/terms and metadata/provider limits.

### Sheet Notes repair and ranked list (17 November 2026)

The owner clarified that column E (Notes) already contains role/description summaries. The importer copies a clear role from the first Notes sentence and literal supported UK place names into missing title/location fields. It never invents a role for company-only/opportunity text. Full Notes remain unchanged and are displayed as “Description from Notes” if no full vacancy description is saved; these summaries are not misrepresented as complete job requirements.

Existing Sheet-linked jobs receive an idempotent local startup repair, without Google calls or a new import/permission. Per-field Notes ownership is tracked in existing SheetLink JSON metadata, so changed Notes can refresh generated fields while manual or official-source replacements remain protected. Raw values/formulas, Notes, job IDs, statuses/history and Google cells are preserved. A later official listing extraction may replace still-Notes-derived fields with source details.

Matching may use available Notes summaries, with an explicit summary-only notice. Notes updates invalidate scores. Jobs has Score active jobs and Preference match (highest) sorting. Batch scoring snapshots at most 500 ready active jobs, skips closed/applied/past-deadline/incomplete jobs, rechecks eligibility-to-score in the worker and reuses current results. No status changes or submissions occur. Stale/missing/inactive scores are never shown as numeric ranked recommendations. Identical pending batches are deduplicated. This is local preference ranking, not personal/legal eligibility.

### Source-identity rollout (19 November 2026)

Link repeat intake using canonical URLs and recognized provider/board/posting identifiers, retaining alias URLs and one application/event history. Supported official Greenhouse/Lever/Ashby URL variants can share a record. Do not trust an arbitrary employer URL's job-ID query parameter without provider/board scope. Conflicting pre-existing identity records require review, not destructive historical merging. Fuzzy same-employer/location close-title matches are hints only; distinct known requisitions/years are excluded. This conservative first stage prioritises avoiding false merges over aggressive cleanup. Source URLs remain traceable in the UI. Migration must preserve existing records and have a verified backup/restore path.

### Owner-controlled matching preferences (19 November 2026)

Settings exposes the existing six weights and preferred role keywords. Require all six integer weights, each 0–100, summing to 100; sponsorship is never a weight. Blank keywords use the existing technology defaults. Changes invalidate cached scores; recalculation is explicit. Display current Good/Poor counts separately from ratings on changed inputs. Ratings support manual adjustments only, with no automatic training; recalculating changed inputs requires a new rating. Preserve other saved settings.

### Manual sponsorship evidence review (19 November 2026)

Role-specific findings may be saved only after explicit owner confirmation, a quote present in saved vacancy description/requirements and a saved listing source for the same job. Notes/company history/licences are insufficient. Bind the review to URL, employer, title, location, dates and vacancy content; changed inputs display Unverified with stale evidence retained for review. Old unbound records remain Unverified. Display traceable quote/source/review time and allow clearing. Quote validation checks provenance, not semantic correctness: the owner reviews all conditions and leaves ambiguity Unverified. No automatic evidence classifier, licence matching, eligibility determination, score change or legal declaration change is introduced.

### Lever discovery delivery (19 November 2026)

Read-only public Lever postings API supports explicit global/EU region, owner-entered employer label and bounded complete-board pagination through the existing fetch/worker guards. Posting URLs must match region, board and UUID. No application endpoint is called. Source-ID intake dedupe preserves one application; malformed/denied/repeated/incomplete pagination saves no partial board. Fixture-tested support is delivered; live Lever and real multi-ATS evaluation remain unverified because cloud API access is blocked. No environment policy changes are authorised by this delivery.

### Regional source-identity isolation (19 November 2026)

Treat Greenhouse and Lever global/EU instances as separate provider-ID scopes. Equal board/ID text across instances is insufficient evidence for automatic merging. Legacy/current URL variants within one instance may still dedupe. Cached-key migrations preserve existing jobs and histories; existing combined records are not automatically split.

### Reviewed secondary listings (21 November 2026)

Allow explicit owner confirmation that a new secondary listing is the same vacancy. Subsequent intake reuses the saved job/application/history; no similarity-only merge. Require current vacancy fingerprint and strict confirmation; serialise simultaneous reviews of the vacancy before checking source identities. Refuse a URL/identity belonging to another saved job and distinct known IDs/regions in the same provider board, considering every primary/secondary source. This does not merge/delete two existing jobs or their histories. Only secondary owner-confirmed links can be removed after confirmation; retain primary/automatic provenance and block removal while URL intake is pending (including another official alias of the same ID) or saved evidence references it. No URL fetch, migration, Sheets write or new dependency is introduced. Fixture/worker/browser verification is not independent live cross-ATS acceptance.

### Exact start-date regression coverage (19 November 2026)

Five additional genuine Marshall Wace snapshots expose three month-first exact start dates and two flexible ranges. The initial held-out failure is retained. Full labelled dates accept day-first/month-first order; partial, impossible or range dates stay unknown. These cases become regression data after the fix; report this consumption and shared-template limitation. The original 30-page manifest stays frozen; expanded 35-page results do not constitute independent multi-ATS or Phase 2 acceptance.

### Local requirement extraction (owner decision, 20 November 2026)

The owner selected local Ollama. Explicit per-job tasks may extract technology/education/experience candidates and verbatim quotes from actual vacancy text only. No Notes, applicant facts, CVs or declarations. Schema/quote validation, local endpoint restriction, bounded retries/context and stale-source protection are required. Current validated technology terms may feed deterministic reviewed-fact overlap; the model never supplies scores, sponsorship confirmation or personal eligibility. Without current extraction the labelled finite-keyword fallback remains. qwen2.5:3b is recommended initially; actual model quality remains unverified and must not be inferred from synthetic protocol tests. No Phase 3 permission is implied.

### Dated register signal (20 November 2026)

A user-downloaded Home Office worker-register CSV may be cached after explicit owner confirmation of official asset reference, publication date and mapping. Display exact organisation-name matches, routes and dated file/source provenance independently of role sponsorship and scoring. Case/whitespace/Unicode composition may normalise; brands, legal suffixes, accents and punctuation must not be guessed. A miss is not proof of no licence, and a hit does not establish role-specific sponsorship, legal employer identity or applicant eligibility. Reject malformed/partial imports atomically. Current file provenance is owner-confirmed upload, not automatic official-source verification.

### Tier 1 source coverage / immigration-neutral matching (20 November 2026)

Ashby public posting-board intake joins Greenhouse/Lever with explicit public-listing visibility and strict source identity checks. Missing/unlisted/private or malformed data is not guessed. No application endpoints. Current Ashby verification is synthetic contract/worker/browser coverage, not live.

Deterministic matching excludes immigration/sponsorship/right-to-work candidates even when a model misclassifies them as skills. This is not a legal eligibility rule. Source candidates remain reviewable; quality evaluation is still needed. Score version changes invalidate previously cached calculations.

### Initial aggregator delivery (20 November 2026)

Reed supports explicit keyword searches through its credentialed public API. Keys stay private/server-side and are scoped to fixed official search/detail endpoints, not URLs/robots/browser/task data. Each run covers the first 20 matches with detailed text, not all results; existing public fetch guards remain. Publication/ad-expiry dates do not establish application deadlines. Official Reed IDs may dedupe URL variants without merging histories. Current real verification is unavailable; fixtures/auth-scope/browser/migration coverage is not a live compatibility claim.

### Fourth public ATS delivery (20 November 2026)

SmartRecruiters supports an explicit company board's first 20 postings and detailed public text through existing guards. Clearly label the bounded page, preserve literal fields and avoid publication-date guesses. Distinguish opaque API IDs from numeric human-listing IDs; enforce official company-scoped listing URLs and keep alias histories intact. Current verification is synthetic contract/worker/migration/browser coverage; live compatibility and independent multi-ATS quality remain unverified.

### Local model identity check (21 November 2026)

Selecting Ollama requires model metadata as well as loopback transport. Before sending public vacancy text, inspect the selected model name via `/api/show`; refuse explicit cloud tags, advertised remote models/hosts and missing/malformed local model metadata. Apply this to native requirements and compatible page extraction, without hosted fallback. No applicant data is added. Tests/metadata validation do not establish semantic-quality acceptance.

### Real legacy-URL regression (21 November 2026)

Two genuine Cloudflare pages exposed source rejection when Open Graph metadata names the legacy Greenhouse host. Recognise equal official provider/board/posting identities across supported URL forms, without crossing global/EU instances or accepting another board/ID/lookalike host. No redirect/network relaxation. Retain initial failures and annotation correction in fixtures/eval/REVIEW_NOV21.md. Current combined set is 40 same-ATS regression excerpts; no new positive dates or independent acceptance claim.

### Complete metadata dates (21 November 2026)

Validate the complete ISO calendar date/timestamp before taking its advertised calendar day. Ranges, trailing prose/junk and invalid times/offsets remain unknown rather than silently using the first ten characters. Preserve valid dates, leap days and timestamp offsets without inventing a start/deadline. This applies to structured JobPosting metadata and Greenhouse API deadline fields; labelled source dates retain their existing range guard.

### Fallback page-model boundary (21 November 2026)

Only requested public vacancy fields may be returned by the fallback page model; owner Notes, URLs, status/legal fields and other extras are rejected. Ground values/dates against the exact bounded text sent to the model, not unseen trailing text. Retain the original source description. Schema/source membership checks are not a semantic-quality certificate.

### Structured posting identity consistency (21 November 2026)

When JSON-LD supplies a URL and both it and the selected source have recognised ATS identities, conflicting posting/board/region/provider identities stop extraction for manual review. Relative references resolve without a fetch. Retain the selected source URL; a publisher/custom URL or arbitrary job-ID query does not establish a new authoritative identity. This is source consistency, not employer verification.

### Fallback selection and hard source conflicts (21 November 2026)

Unsupported provider selectors stop with a configuration error, never silently choose hosted extraction. Preserve the documented default and explicit ollama/openai_compatible selections. A known Greenhouse page identity mismatch is a hard NeedsInput stop, not a reason to ask a model to override it.

### Focused model diagnosis (23 November 2026)

Allow an explicit reviewed-case selection in the public model checker. Non-selected cases remain NOT TESTED; full metrics unknown and Phase2 unaccepted. A focused case pass is not full-suite success. Technology candidates must be named role-specific tools/platforms, excluding general abilities and company/product marketing. Semantic instruction changes do not relax source/quote/schema constraints or change frozen review labels.

### Explicit New Grad titles (23 November 2026)

Recognise explicit New Grad/New-Grad titles as graduate role-level signals. Senior/manager titles still take precedence; internships remain Unverified even when their title includes Graduate/New Grad. This is role classification, not personal eligibility. Score version changes invalidate prior scores for recalculation, preserving job fields/application events and retaining stale feedback as such. Fresh real control labels and the first failed prediction remain recorded; no positive exact-date or multi-ATS claim follows from this fix.

### Extraction-rule cache binding (23 November 2026)

Bind cached public requirements to both source context and extraction-rule version. Changed instructions/schema/options/input bound require a fresh extraction before previous candidates can influence ranking. Preserve legacy payloads, Notes and application history; never silently reuse stale semantic output. Public evaluation reports may record the non-personal extractor signature. No personal/legal data is added to model input.

23 November verification note: additional genuine same-ATS controls exposed explicit Early Career/manager-intern role errors and a description-H1 parsing failure. These are fixed under the existing role-label rubric with retained initial reports;48-page consumed regression is not independent Phase2 acceptance. No scope or agreed target change.

Geographic extraction note: when Greenhouse gives only a work mode or no header location, the explicit Available Locations body paragraph/list may supply the location. Concrete headers and existing owner content remain untouched. Post-inspection geographic-label refinements are separate from the original literal-header fixtures; no independent accuracy claim.

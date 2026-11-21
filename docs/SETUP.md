# Run and configure the local app

These instructions describe the current code. Run on the owner's own computer; the project remains local through Phases 1–5. Use the existing checkout and preserve `.env`, `.local/` and `storage/`.

## Latest update: Phase 2 migrations (20 November 2026)

The latest migrations include source identities, content-bound manual sponsorship reviews, public requirement candidates, the dated sponsor-register cache and discovery-search configuration. Stop the app with Control+C, pull the branch, then use `python3 scripts/dev.py --migrate` from the project root. The launcher loads your existing private .env, creates and restores/verifies a backup of an existing SQLite database/storage into ignored `.local/migration-backups`, applies migrations to that configured DB and starts services. It refuses when the worker is running or backup verification fails. Regular later starts still use `python3 scripts/dev.py`. Keep the encryption key separately. No new dependencies. The API now fails early with this instruction if the schema is behind.

## Start on macOS in VS Code

Requirements: Python 3.12+, uv, Node.js 24 and npm. The owner uses a Mac and has already run the published app. If `uv` is missing, install it with `brew install uv` when Homebrew is available, then reopen the terminal and check `uv --version`. Dependency/runtime failures are setup work, not a reason to recreate or discard private data.

From the repository root, first-time setup. Run commands one at a time and stop at the first error; a later successful command does not fix an earlier failed installation:

```sh
python3 scripts/init_local.py
cd apps/api
uv sync --frozen
cd ../web
npm ci
cd ../..
python3 scripts/dev.py --migrate
```

Open `http://127.0.0.1:3000` in a browser on the same computer. The dashboard opens directly; no token entry is required. The combined launcher loads the private root `.env` and starts API, worker and web processes. Keep that terminal open. Click the terminal and press **Control+C**, not Command+C, to stop.

For later runs, from the repository root:

```sh
python3 scripts/dev.py
```

After completed work is pushed, stop the app before updating:

```sh
git pull --ff-only origin dev/phase-1
```

Do not overwrite local changes if Git reports a conflict. Refresh Python dependencies with `cd apps/api && uv sync --frozen` only if their lockfile changed, and run `npm ci` from `apps/web` if the JavaScript lockfile changed. Return to the repository root and start `python3 scripts/dev.py --migrate` for an update containing migrations. That launcher loads the private configuration and verifies a backup before upgrading an existing database. Later ordinary starts use `python3 scripts/dev.py`.

Keep ports 3000 and 8000 on localhost. The API token is generated and used only by the local servers. Do not paste it into chat, browser storage or committed files. `scripts/init_local.py` preserves existing `.env` values; it is not a credential rotation tool.

## Useful verification commands

From `apps/api`:

```sh
uv run --frozen pytest
uv run alembic check
```

From `apps/web`:

```sh
npm run typecheck
NEXT_TELEMETRY_DISABLED=1 npm run build
```

After the frontend build, from `apps/api`:

```sh
uv run --frozen --group browser python ../../scripts/smoke_browser.py
```

The browser check starts production test services on ports 8001/3001 with disposable DB/storage. It must not use the owner's database. It needs Chromium: use system `chromium`, set `CHROMIUM_EXECUTABLE`, or use the supported `uv run --group browser playwright install chromium` installer. Artifacts stay in ignored `.local/`. The current reference-inspired UI has production desktop/mobile smoke coverage for core pages, filters, navigation and disclosures, plus real-worker pasted-HTML extraction, TXT CV review/download and settings backup/CLI restore. See STATUS.md for the exact evidence and remaining workflow limits.

## Google Cloud: read-only development-copy setup

The owner reports successful Google connection and all 20 development-copy jobs imported on their Mac; this cloud workspace has not independently inspected that private session. Configure this on the same computer that runs the app, because the OAuth callback is a loopback address. The original tracker is blocked by the code. Read-only OAuth permission can read spreadsheets available to the account; the configured development-copy ID is the app's additional restriction. The OAuth scope itself is not limited to one spreadsheet.

1. In Google Cloud Console, create or select a project dedicated to this app.
2. Open **APIs & Services → Library** and enable **Google Sheets API**. No Drive API is required for this read-only import.
3. Configure the **OAuth consent screen / Google Auth Platform**:
   - Branding/app name: a clear development name such as `Job Tracker Development`.
   - Supply your own support and developer contact email in Google's console.
   - Audience: **External**, with publishing status **Testing** for a personal Google account.
   - Add the Google account you intend to use as a **test user**.
   - Data access/scopes: request only `https://www.googleapis.com/auth/spreadsheets.readonly`. Do not add the broader `spreadsheets` or Drive scopes.
4. Under **Credentials / Clients**, create an **OAuth client ID** of type **Web application**. Add this exact authorised redirect URI:

   ```text
   http://127.0.0.1:8000/oauth/google/callback
   ```

   Use `127.0.0.1`, not a different hostname or port. No JavaScript origin is required by this server-side code-exchange flow.
5. Download the client JSON. In the local project, create the ignored `.local` folder if needed. Move the downloaded file there and rename it:

   ```text
   .local/google-oauth-client.json
   ```

   From the project root, restrict its permissions:

   ```sh
   chmod 700 .local
   chmod 600 .local/google-oauth-client.json
   ```

   Do not upload this file in chat or commit it. The default loader expects Google's `web` client object and the redirect URI above. If you choose another private location, set `GOOGLE_OAUTH_CLIENT_FILE` to its absolute path in the root `.env`. Never put it in a `NEXT_PUBLIC_*` variable.
6. Run `python3 scripts/init_local.py` if the local `.env` has not been initialised. It creates a private local OAuth encryption key without printing it. Preserve that key separately from backups; encrypted tokens cannot be restored without the original key. Restart the app after configuration changes.
7. In the original Sheet, use Google's **File → Make a copy** yourself and give the copy a clear development name. Do not configure the original ID in the app. No app operation should touch the original.
8. In the app's **Settings**, enter the development-copy ID, exact tab name and actual header-row number. Confirm that it is a test copy. Save the mapping, then choose **Connect Google** and sign in as your intended test user. After consenting to read-only access, return to the app.
9. Run **Import test copy**. The next verification must compare imported/snapshotted row counts and values against that copy, including incomplete rows and formula columns. A synthetic unit test is not proof this live import passed.

The owner already supplied these headers:

| App field | Exact Sheet header |
|---|---|
| company | Company |
| deadline | Deadline |
| url | Application Link |
| status | Status |
| notes | Notes |

`Deadline alert` and `Days left` are preserved and must not be write targets. There is no dedicated role-title column: column E, Notes, supplies literal role/location summaries. Clear first-sentence titles and supported place names populate missing fields; company-only entries retain Role not provided. Original row data/Notes are preserved. Source status text is retained separately and cannot establish a confirmed APPLIED state. Sponsorship claims in Notes do not become confirmed sponsorship.

The owner supplied development-copy ID `1xjj0CEMzWrQS7sROq7QHvyoaLle67vkeWn9lIXv6bEY`, tab `sheet1` (use the exact case displayed in Google), header row `1`, then reported all 20 jobs imported and approved copy-only status writes. Live write verification is still pending. Read-only continues to work without any scope change.

## Backup and restore

Use Settings to choose a backup directory outside `storage/`, save it, and request **Back up and verify restore**. Scheduled backups run only while the app is open; overdue scheduled work catches up once rather than duplicating every missed run. Each backup is restored and checked before being reported successful.

To inspect a restore into a **new** folder, from `apps/api`:

```sh
uv run python -m app.services.backup_cli restore \
  --archive /absolute/path/to/backup.zip \
  --destination /absolute/path/to/new-restore-folder
```

Substitute real local paths. This command checks archive contents/checksums and DB integrity and refuses to overwrite an existing destination. It does not switch the running app to that database. Stop all services and inspect the restored DB/files before any deliberate data switch. Keep the original data and encryption key intact; do not treat an untested laptop restore as complete just because cloud tests passed.

## Desktop deadline reminders on Mac

On Dashboard, choose **Enable desktop reminders** and allow the browser permission prompt. In macOS System Settings → Notifications, allow notifications for that browser (and website, if listed); Focus settings may silence them. Reminders are optional and run only while this browser tab and the local app are open. They cover active jobs due within seven days, once per job per UK day in that tab session. Reloading starts a new session; choose Enable again. Use **Pause desktop reminders** to stop. Denied/unsupported notifications leave the deadline view available. No email, OS background service or closed-browser scheduling is implemented.

## Optional approved status write-back on the development copy

You can keep Sheets read-only by leaving `SHEETS_WRITE_COPY_ID` unset. There is no automatic write scheduling. The owner approved development-copy status writes after reporting the successful import; this approval does not permit touching the original tracker. The owner later separately authorised Phase 2 while deferring this live write test; keep Sheets read-only during current Phase 2 work.

To perform the remaining live acceptance test on your Mac:

1. Stop the app with Control+C and pull `dev/phase-1`. In your private root `.env`, add exactly one line (or update it if already present):
   ```text
   SHEETS_WRITE_COPY_ID=1xjj0CEMzWrQS7sROq7QHvyoaLle67vkeWn9lIXv6bEY
   ```
   This ID must match Settings. Do not set it to the original ID, which remains blocked even if entered here.
2. In Google Auth Platform → Data Access, add `https://www.googleapis.com/auth/spreadsheets` for the existing testing client. No Drive scope is needed. This Google permission can edit spreadsheets available to the account; the app additionally restricts writes to the configured copy. The OAuth scope itself cannot restrict access to a single spreadsheet.
3. Start `python3 scripts/dev.py`. In Settings → Google Sheets choose Connect Google again and grant the requested permission. The existing read-only grant cannot perform writes. Keeping both the existing readonly and new spreadsheets grant is supported; unrelated permissions are rejected.
4. Import the test copy again to establish a current baseline. Choose one row whose source status is Not Started and whose status cell contains plain text, not a formula. Record its row number, current status, notes, deadline, formula cells and formatting. Ensure there are no other pending local status changes: the manual sync writes all changed linked statuses, not only the currently open job.
5. In that job's app details, change Discovered to Shortlisted. In Settings choose Write changed statuses to copy. Background tasks should report **1 cell written**. In Google verify only that row's Status cell changed to Shortlisted; Notes, deadlines, formulas, formatting and all other rows must remain unchanged.
6. Run the same write-back once more without changing anything. Expect **0 cells written**. Send the task counts and the comparison result, never credentials or callback URLs. Phase 1's live single-cell criterion is not passed until this comparison succeeds.

Writes use RAW values on one cell per request, with header, row-identity, formula and target-value checks. Avoid editing/sorting the copy during sync: these checks cannot make Google's separate reads and write atomic. Duplicate URLs and formula status cells are skipped; moved/concurrently changed targets halt further writes. An uncertain outcome needs inspection and is never automatically retried.

Current write-back updates existing linked statuses only: it does not append new app jobs, change deadlines/sponsorship, write Notes, or set APPLIED. Those broader sync behaviours are not delivered by this slice. To stay read-only, leave the setting unset and retain the current grant. If already granted broader permission, removing the setting blocks its use in this app; reconnect read-only (and revoke the old Google grant if necessary) to reduce Google's permission too.

## Phase 2: manual public-board discovery

The owner authorised Phase 2 with the Phase 1 live write test deferred. Keep Google Sheets read-only. In Settings → Job discovery, enter the employer's Greenhouse board **slug**, not its URL. It is the identifier in a URL such as `https://job-boards.greenhouse.io/BOARD`. No sources are seeded or fetched automatically. Review the source's terms before enabling it; the checkbox enables manual task requests only.

For a permitted public API fetch, add `boards-api.greenhouse.io` to your existing comma-separated `URL_FETCH_ALLOWED_HOSTS` in the private root .env, preserving any hosts already approved. Restart the app. Add/enable the chosen source, click Discover jobs from that source, then inspect Background tasks and Jobs. Imports run in the worker, dedupe canonical URLs and leave sponsorship UNVERIFIED. This adapter imports the whole chosen board; use current preference scores to prioritise UK/junior technology roles. Unsupported/missing dates stay unknown, and absent API company names are explicitly shown as Employer not provided. No submissions, Sheets writes, profile data or hosted LLM calls are involved.

The shared fetcher requires publicly resolving addresses, explicit host approval, accessible robots.txt and allowed crawl rules. It bounds responses to 1 MB, rate-limits, and stops on redirects, 401/403/429 or robots denial. Large boards may need a later bounded pagination/detail adapter; this version fails rather than silently truncating them. Live verification on 17 November 2026 fetched a Graphcore vacancy and imported 60 Monzo postings twice through a disposable API/worker: first 60 added, then 0 added/60 duplicates. No owner storage was used.

The owner published the Greenhouse network policy. On 17 November 2026 current environment status reported both hosts permitted and the policy enforced; fresh robots/page/API fetches passed. No environment settings were changed or republished during this delivery. Local .env host permission and cloud network access remain separate controls. In a proxy-managed environment with unavailable local DNS, only these two fixed HTTPS sources may delegate DNS to the configured HTTPS proxy; arbitrary hosts, private DNS results, nonstandard ports and insecure HTTP remain blocked.

Real-page evaluation instructions and manifest format are in `fixtures/eval/README.md`. The manifest now contains 30 real, reviewed snapshots. From apps/api run:

```sh
uv run --frozen python -m app.services.evaluation --manifest ../../fixtures/eval/manifest.json
```

An empty dataset exits 2 and reports NOT READY; it is not a benchmark pass. That prerequisite is now met for the initial development set; separate held-out validation is still needed. Synthetic parser/runner tests are only software tests, not real job postings or evaluation evidence. The owner accepted initial 90% field-accuracy targets; zero false CONFIRMED_YES remains required regardless of whether sponsorship affects job selection.

## Calculate a preference match

Open a job's details and choose **Calculate preference match**. Keep the worker running; the card displays a score out of 100 and **Why this score?** explains every criterion and cites reviewed fact IDs. Add and explicitly review your facts in My Profile to make the skill/experience components useful. Use **Good match** or **Poor match** to save a rating; ratings do not automatically change weights yet.

The score is a preference heuristic, not an eligibility decision, sponsorship check or probability of success. Changing source fields, reviewed facts or preferences makes old results stale; recalculate before relying on them. Source/Notes instructions never change legal declarations or application statuses.

Existing Sheet imports now repair missing titles/locations automatically from stored Notes on API startup. No new Google permission or import is needed for already imported data. In details, Description from Notes shows the original summary when a full description is absent. Company-only rows still require an actual role title. You can paste the existing URL on Dashboard to enrich details with a supported full listing. Existing Notes, statuses and populated fields are preserved. Matching can use a Notes summary when a real role title is available, with an explicit summary-only notice. Missing role/summary data is shown as Needs details rather than a misleading zero score.

To reproduce the latest 38-page field/role regression from apps/api:

```sh
uv run --frozen python -m app.services.evaluation --manifest ../../fixtures/eval/manifest-nov20.json --role-classification
```

Historical reports are stored under fixtures/eval/reports; this command prints a fresh report. Original 30/35 manifests stay frozen. See fixtures/eval/REVIEW_NOV20.md for the new controls and known coverage limits. This regression does not accept Phase 2. For the current migrations, use the backup-verifying update launcher at the top of this guide. Sheets remains read-only; no Google permission change is needed.

## Apply the Notes fix to existing jobs on Mac

Stop the app with Control+C, then from the project root:

```sh
git pull --ff-only origin dev/phase-1
python3 scripts/dev.py
```

No dependency/migration update is required. API startup fills missing fields from already stored Notes for Sheet-linked jobs. You do not need to paste the 20 rows, add a Role column, reconnect Google or re-import unchanged data. Cloud code delivery cannot directly change the separately running Mac app; this restart applies the repair locally.

In tests using all 20 supplied public summaries, 19 have clear role titles. The company-only startup opportunity has no actual title, so it remains Role not provided while its Notes are visible. Supported explicit locations are copied literally; no location/eligibility is guessed. Full original Notes and imported statuses are preserved. Fields manually edited or replaced by official listing data are protected from later Notes refreshes. Newer edits made in Google after the last import still require Import test copy (read-only).

On Jobs, choose **Score active jobs**, wait for Background tasks, then select **Preference match (highest)**. Current scores appear in the table; stale, inactive and incomplete records show text labels. Batch scoring excludes already applied/closed/past-deadline jobs and handles up to 500 ready active rows. Existing unchanged scores are reused; job details still explain scores and accept individual ratings. Scores based on Notes are explicitly limited summaries, not verified requirements or application eligibility. Google write permission is not needed.

## Source identities and duplicate review

The same recognised Greenhouse, Lever or Ashby posting ID across supported official URL forms links to one existing job/application. Original/additional URLs are retained under Sources and possible duplicates in job details. Existing job IDs, owner edits, application events, Notes and Sheet snapshots are not merged or deleted. Duplicate identity conflicts among existing records stop intake for review (Sheet rows still preserved). Aliases retain old URLs after a manual primary-URL edit, and cannot be reassigned to a different tracked job.

Close titles with the same normalized employer/location can appear as review-only hints. Different programme numbers/years and different known requisitions within the same ATS board are excluded from these hints. Text similarity never automatically combines existing records or confirms that two openings are the same. Current intake identity support is not a claim of live Lever/Ashby discovery support.

For a second listing that is not saved on another job, open **Link another listing for this vacancy** in that panel. Read both listings, enter its URL and confirm it is the same vacancy. Future imports of that URL reuse the existing job/application, preserving owner content, Notes and events. This saves a reviewed URL without fetching it. Distinct known IDs/regions on the same provider board are refused, as are URLs/identities owned by another saved job. Review those records separately; the control does not delete or merge existing histories.

**Remove reviewed link** removes only a secondary manually linked URL after confirmation; it retains imported content and the job/history. Primary/automatic provenance cannot be removed here. A pending URL import or saved sponsorship evidence using that URL blocks removal until reviewed/cleared. A changed vacancy requires a fresh source review. No migration or new dependency is needed for these controls.

## Manual sponsorship evidence review

In job details, expand Review role-specific evidence. Read the source and save a complete quote from the saved vacancy description/requirements, choose its saved listing URL, select an explicit Offered/Not offered finding, and confirm your review. Notes alone cannot establish policy. Leave unclear or conditional policy Unverified. The app checks quote provenance and your confirmation, not the statement’s meaning or immigration eligibility. Editing vacancy identity/content/location/dates invalidates the review. Previous evidence remains visible until reviewed again or cleared. Findings do not affect preference scores; sponsor licences remain unchecked.

## Lever public discovery (Phase 2)

After pulling, use `python3 scripts/dev.py --migrate` to preserve/upgrade existing source settings. In Settings → Job discovery choose Lever, enter the board slug and the exact employer name shown on that board, then choose Global (`jobs.lever.co`) or EU (`jobs.eu.lever.co`). Review source terms before enabling manual imports.

For Global add `api.lever.co`, or for EU add `api.eu.lever.co`, to your existing comma-separated private `URL_FETCH_ALLOWED_HOSTS`, preserving other entries. Restart afterwards. Do not share that file. Network access/robots approval is also required; this cloud currently blocks the Lever API, so its live import is not verified here. No broader network grants were published. No credentials or application-form access are required.

Imports use bounded pagination and fail before saving a partial board if later pages are denied, repeated or exceed the limit. Invalid individual postings are counted. Duplicate ATS posting IDs preserve one application and traceable source URLs. Missing/partial dates stay unknown; sponsorship stays Unverified until separate explicit evidence review. Sources are never seeded and automatic discovery is not scheduled. Synthetic contract fixtures are test-only, not real job recommendations.

## Local Ollama requirement extraction (20 November 2026)

The owner chose local Ollama. The initial qwen2.5:3b failed the real development checks. For the reported 16 GB Mac, **qwen2.5:7b** is the next candidate, not a quality-verified model. It has already been downloaded on the owner’s Mac; only pull it if missing. Install/open the official Ollama Mac app from https://ollama.com/download/mac, then in Terminal:

```sh
ollama pull qwen2.5:7b
```

Keep Ollama running. Add or update these entries in the private root `.env`, preserving every other setting and avoiding duplicate entries:

```dotenv
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
LLM_BASE_URL=http://127.0.0.1:11434/v1
```

No API key is needed for this local connection. Do not paste your full `.env` into chat. Stop the tracker with Control+C, pull the latest branch and run `python3 scripts/dev.py --migrate` from the project root. This delivery adds the source-bound requirements cache. There are no new project dependencies. When Ollama is already running through the Mac app, do not start a duplicate server.

In job details → Source requirements, click **Extract requirements locally**. The actual vacancy description is required; Notes are excluded. The worker calls the native local API with a schema and no tools, validates copied terms/quotes, then displays them with their model name. Recalculate the preference score afterwards. Scoring remains deterministic and uses reviewed facts; no applicant facts, CVs or legal values are sent to the model. Education/experience candidates do not establish personal eligibility. If extraction is missing/stale, matching retains the explicitly labelled finite-keyword fallback.

The first 16000 source characters are processed with bounded context/output; truncated inputs are flagged. Source changes invalidate the cache. Three invalid responses stop without saving; an unavailable model/server asks for setup rather than retrying indefinitely. Remote/LAN model URLs are rejected for this task. Current automated coverage uses a synthetic local HTTP fixture; **actual revised-prompt qwen2.5:7b quality is not yet verified**. Do not treat quoted source membership as semantic correctness or Phase 2 acceptance.

## Sponsor register CSV (separate informational signal)

After pulling use `python3 scripts/dev.py --migrate`. In Settings → Sponsor register, open the official Home Office worker-register page, download its CSV on your Mac and copy the CSV asset link. Choose the file, paste that `https://assets.publishing.service.gov.uk/media/.../*.csv` link and enter the publication date shown by the source. Check the column names against your file; defaults are Organisation Name, Route and Town/City, with Town/City optional. Confirm the provenance/date/mapping, then Import sponsor register. No Google permission is needed.

The worker validates the entire CSV before replacing the public cache. A malformed file keeps the previous snapshot active. Limit: 50 MB/one million rows, UTF-8 CSV. Uploaded files and source/date/hash metadata are included in backups. Current tests use synthetic CSVs; the actual official file has not been fetched/verified by this cloud environment.

Job details show an exact registered-name match with routes/towns/date/source, independently of role sponsorship. Brand/legal-name differences can hide a match; punctuation/accents/legal suffixes are not guessed. A name match does not establish this role’s policy or your eligibility and has no score weight. This is owner-confirmed file provenance, not automatic online verification. No snapshot means Not checked. Old dates remain visibly old; do not assume current licence/visa rules.

## Evaluate the local model before relying on extracted terms

With Ollama running, the selected model installed and the model entries above saved in your private `.env`, run this from the **project root**:

```sh
python3 scripts/dev.py --check-model
```

This loads the same model choice as the app (explicit shell model settings still take precedence). It passes only the local-model selectors and minimal runtime settings to the public evaluation process, excluding database/app/OAuth/API credentials. It does not start the tracker, migrate or open its database, profile, Notes or CVs. The native connection enforces loopback and does not use shell proxies. App access-token setup is not needed for this public-only check; API dependencies must already be installed.

The default check makes one response attempt per case and stops after the first failed check. Remaining cases are NOT TESTED, never counted as passing or assigned full-set accuracy. It prints completed/planned counts, a rejection reason and safe schema field/type codes, then the relative path of a new report under `.local/requirements-check-*.json`. Existing reports are never overwritten. It validates source hashes, minimum named-technology expectations, empty cases and company-marketing controls. The field/role manifest has 38 pages; this separate model subset is still nine, not full semantic coverage. No real model was available during cloud verification; the actual shortcut correctly reported all nine NOT TESTED and exit 2.

Exit 2 means setup/input unavailable or NOT TESTED. An unavailable local server stops further model calls and leaves quality metrics unknown, not a fabricated zero-quality result. Exit 1 means schema/grounding or the reviewed minimum-term/empty-case checks failed. Exit 0 passes these limited development checks, not every requirement or full Phase 2 acceptance. Inspect quotes and the explicit coverage limits. No real model was available in the cloud run, so its semantic quality remains unverified.

## Ashby public discovery

Settings → Job discovery now includes Ashby. Enter the board slug and the employer name exactly as shown on the public board. Review its terms, add `api.ashbyhq.com` to your existing private URL_FETCH_ALLOWED_HOSTS without removing other entries, and restart. This cloud's policy has not been changed; actual Ashby access remains unverified here.

Only explicitly listed public rows with matching official board/UUID listing URLs are imported. Unlisted/missing visibility, off-board URLs and malformed entries are skipped; application/private ATS endpoints are never called. Dates come only from complete labelled vacancy text; publishedAt is not a deadline. Current support is contract/worker/browser tested with synthetic fixtures, not a live compatibility claim. No new schema/dependency for this adapter.

The matching scorer also excludes immigration/sponsorship/right-to-work terms even if a model incorrectly places them among technology candidates. It never derives your legal status. This score-version update makes older results stale; recalculate active-job scores after pulling.

## Reed aggregator search

Reed is an optional, credential-gated public API source. Obtain a jobseeker API key from https://www.reed.co.uk/developers/jobseeker after reviewing its terms. Put it only in the private root `.env` as `REED_API_KEY=...`; never send the key in chat or enter it in the website. Add `www.reed.co.uk` to your existing private URL_FETCH_ALLOWED_HOSTS, preserving other approved hosts. The cloud network policy is separate and has not been changed. Restart with `python3 scripts/dev.py --migrate` after pulling this release (new search configuration/cached-ID migration).

Settings → Job discovery → Reed search takes keywords instead of an employer board slug. Employer/location come from actual API records. Without a private key the import button is disabled; the key itself is never sent to the browser. Enable the source for manual requests only after reviewing terms/access.

Each run reads the **first 20 matching ads**, then detailed API text. It is not all search results; change the query to explore other matches. Existing rate/robots/size/denial guards apply, so detailed imports can take several minutes while the app stays open. No automatic discovery/retry is scheduled. Posting date/advert expiry are not guessed as application deadlines. No sponsorship filter or score penalty. Known Reed IDs dedupe hostname/title-slug variants while preserving histories; conflicts among existing records need review.

Live Reed credentials/official responses were unavailable in cloud. Current verification is synthetic contract/worker/auth-scope/migration/browser coverage. No Google/OAuth changes are needed. Use the existing `--migrate` backup-verifying launcher; old sources keep empty search-query defaults.

## SmartRecruiters public discovery

Settings → Job discovery → SmartRecruiters takes the company identifier from its public board URL (for example the `CompanyIdentifier` in `https://jobs.smartrecruiters.com/CompanyIdentifier/...`) and the employer name exactly as displayed. Review its terms, then add `api.smartrecruiters.com` to your existing private URL_FETCH_ALLOWED_HOSTS without removing other approved hosts. No API key is used. Cloud policy is separate; no grant was changed here.

Imports read the **first 20 company postings**, then their detailed public API text. This is not the entire board, and repeated runs revisit the page. Existing robots/rate/size/access guards apply, so detail requests can take several minutes. The configured company and public listing ID must match; unsupported links/data are skipped instead of guessed. Publication dates do not become deadlines; sponsorship stays informational. No automatic schedule or portal form interaction.

Pull and start with `python3 scripts/dev.py --migrate`; the new cached-identity migration preserves jobs and histories. Current verification is synthetic contract/worker/migration/browser coverage, not live SmartRecruiters compatibility. No new dependencies or Google consent are required.

Repeated discovery clicks reuse an existing queued/running task for that source. A finished import can be explicitly requested again; this does not add retries or a schedule. Native local Ollama connections ignore shell HTTP proxy settings and never follow redirects.

The local-model report now labels limited content checks separately from schema-valid output: PASSED/FAILED/NOT TESTED per case and an overall development_checks_passed value. Schema-valid but incorrect/missing terms fail these checks. No-server cases remain unknown, not passed; Phase 2 acceptance remains separate. The model subset is still nine reviewed cases, not all 38 field/role pages.

Backup/restore validation requires the existing version-1 manifest, its database entry and the supported DB/storage layout; incomplete, unsupported or duplicate-member archives are rejected without a restored destination. SQLite snapshot paths are URI-encoded so filenames with `#`, literal percent escapes or spaces identify the same database as the app driver. Backups still restore into a **new** folder only. These checks do not replace the outstanding Mac operational restore check.

The current scoring version excludes additional known leave/residency/settlement/work-rights candidates and separator variants from technology scoring. Existing preference scores become stale after pulling; choose **Jobs → Score active jobs** to recalculate. Source quotes are retained for review. This lexical guard does not establish model semantic quality or legal eligibility.

## Model check says NOT TESTED

Open Ollama on the Mac, then run `ollama list`. If the configured model is missing, run `ollama pull qwen2.5:3b`. Test generation with `ollama run qwen2.5:3b "Reply with OK"`, then retry `python3 scripts/dev.py --check-model` from the project root. If the command is unavailable, the Mac app binary is `/Applications/Ollama.app/Contents/Resources/ollama`; use it in place of `ollama`. Keep the app running.

The new check prints a safe reason code: server_unreachable means connection failed; timed_out suggests warming the selected model first; model_or_endpoint_missing is a 404 and requires checking model installation and local address; structured_request_rejected suggests checking Ollama/model schema support. Access/busy/runtime/redirect failures have separate hints. These are setup/transport diagnostics, not semantic quality scores. No response body, credential or private config URL is printed. The first unavailable request stops further case calls and leaves metrics unknown.

## Slow or failed model checks

The owner’s Mac run of qwen2.5:3b produced only 1/9 schema/grounding-valid responses (minimum term recall 0.1; empty-case accuracy 0.0). This is a real failed model run; the exact rejection causes were not recorded by that older check. Do not certify the model from a successful install or a short OK response.

Pull the latest branch, then use `python3 scripts/dev.py --check-model`. It now makes one response attempt per case and stops on the first quality failure. Codes distinguish output_limit, incomplete_response, schema_invalid, quote_not_in_source, term_not_in_quote, duplicate_term and response_shape. Schema paths/types are shown without response values. Skipped cases remain NOT TESTED and aggregate metrics stay unknown. The tracker’s actual per-job extraction retains its existing initial attempt plus at most two retries; only the public diagnostic is shortened.

`python3 scripts/dev.py --check-model-full` explicitly requests the slower all-case diagnostic with the normal validation retries. Control+C cancels a check without starting/migrating/changing the tracker database. A report is written after a completed check; cancelling before completion may leave no report.

For the owner’s 16 GB Mac, qwen2.5:7b is a larger candidate, not a verified replacement. Download with `ollama pull qwen2.5:7b`, then test it without changing saved settings:

```sh
LLM_MODEL=qwen2.5:7b python3 scripts/dev.py --check-model
```

Only after reviewing its results should you change the private .env model setting. Neither fast-check success on a subset nor schema validity alone accepts Phase 2.

## Ollama opens a cloud chat

Bare `ollama` may open a cloud model. Exit that chat with `/bye`, then select the downloaded local model explicitly:

```sh
ollama run qwen2.5:7b "Reply with OK"
LLM_PROVIDER=ollama LLM_MODEL=qwen2.5:7b python3 scripts/dev.py --check-model
```

The second command runs from the repository root, separately from the chat. Keep Ollama open. The tracker checks `/api/show` with only the model name before sending vacancy text; cloud tags, remote aliases and unverifiable metadata stop with a setup message. A local loopback URL alone does not establish local inference. A successful model download/OK reply is not a passed requirements check. No OAuth change, credential sharing or new model download is needed if qwen2.5:7b is already installed.

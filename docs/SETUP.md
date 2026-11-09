# Run and configure the local app

These instructions describe the current code. Run on the owner's own computer; the project remains local through Phases 1–5. Use the existing checkout and preserve `.env`, `.local/` and `storage/`.

## Start on macOS in VS Code

Requirements: Python 3.12+, uv, Node.js 24 and npm. The owner uses a Mac and has already run the published app. If `uv` is missing, install it with `brew install uv` when Homebrew is available, then reopen the terminal and check `uv --version`. Dependency/runtime failures are setup work, not a reason to recreate or discard private data.

From the repository root, first-time setup. Run commands one at a time and stop at the first error; a later successful command does not fix an earlier failed installation:

```sh
python3 scripts/init_local.py
cd apps/api
uv sync --frozen
uv run alembic upgrade head
cd ../web
npm ci
cd ../..
python3 scripts/dev.py
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

Do not overwrite local changes if Git reports a conflict. Refresh Python dependencies with `cd apps/api && uv sync --frozen`, run `uv run alembic upgrade head` there if migrations changed, and run `npm ci` from `apps/web` if the JavaScript lockfile changed. Return to the repository root and start `python3 scripts/dev.py`.

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

`Deadline alert` and `Days left` are preserved and must not be write targets. There is no dedicated role-title column; the current import uses the explicit unknown label `Role not provided` and retains original row data. Source status text is retained separately and cannot establish a confirmed APPLIED state. Sponsorship claims in Notes do not become confirmed sponsorship.

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

You can keep Sheets read-only by leaving `SHEETS_WRITE_COPY_ID` unset. There is no automatic write scheduling. The owner approved development-copy status writes after reporting the successful import; this approval does not permit touching the original tracker or starting Phase 2.

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

For a permitted public API fetch, add `boards-api.greenhouse.io` to your existing comma-separated `URL_FETCH_ALLOWED_HOSTS` in the private root .env, preserving any hosts already approved. Restart the app. Add/enable the chosen source, click Discover jobs from that source, then inspect Background tasks and Jobs. Imports run in the worker, dedupe canonical URLs and leave sponsorship UNVERIFIED. This first adapter imports the whole chosen board; UK/junior preference ranking is not yet implemented. Unsupported/missing dates stay unknown, and absent API company names are explicitly shown as Employer not provided. No submissions, Sheets writes, profile data or hosted LLM calls are involved.

The shared fetcher requires publicly resolving addresses, explicit host approval, accessible robots.txt and allowed crawl rules. It bounds responses to 1 MB, rate-limits, and stops on redirects, 401/403/429 or robots denial. Large boards may need a later bounded pagination/detail adapter; this version fails rather than silently truncating them. Live API behaviour is not verified yet.

The cloud policy currently denies `boards-api.greenhouse.io` and `job-boards.greenhouse.io`. A saved environment draft adds only those two domains and updates stale startup guidance. **Saved is not applied**: review/save the draft in environment settings, then Publish as requested by the product. Recheck status and perform a fresh permitted fetch before claiming live discovery works. Local .env host permission and the cloud network policy are separate controls.

Real-page evaluation instructions and manifest format are in `fixtures/eval/README.md`. The manifest is currently empty. From apps/api run:

```sh
uv run --frozen python -m app.services.evaluation --manifest ../../fixtures/eval/manifest.json
```

An empty dataset exits 2 and reports NOT READY; it is not a benchmark pass. Matching waits for about 30 real reviewed postings. Synthetic parser/runner tests are only software tests, not real job postings or evaluation evidence. Proposed numerical thresholds were not accepted yet; zero false CONFIRMED_YES remains required regardless of whether sponsorship affects job selection.

# Run and configure the local app

These instructions describe the current code. Run on the owner's own computer; the project remains local through Phases 1–5. Use the existing checkout and preserve `.env`, `.local/` and `storage/`.

## Start on macOS in VS Code

Requirements: Python 3.12+, uv, Node.js 24 and npm. The owner uses a Mac and has already run the published app. If `uv` is missing, install it with `brew install uv` when Homebrew is available, then reopen the terminal and check `uv --version`. Dependency/runtime failures are setup work, not a reason to recreate or discard private data.

From the repository root, first-time setup:

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

The browser check starts production test services on ports 8001/3001 with disposable DB/storage. It must not use the owner's database. It needs Chromium: use system `chromium`, set `CHROMIUM_EXECUTABLE`, or use the supported `uv run --group browser playwright install chromium` installer. Artifacts stay in ignored `.local/`. The unfinished UI redesign is not yet verified; see STATUS.md before interpreting an old test pass.

## Google Cloud: read-only development-copy setup

No live Google connection is verified. Configure this on the same computer that runs the app, because the OAuth callback is a loopback address. The original tracker is blocked by the code. Read-only OAuth permission can read spreadsheets available to the account; the configured development-copy ID is the app's additional restriction. The OAuth scope itself is not limited to one spreadsheet.

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

The development-copy ID, tab and header-row number are still unknown; do not guess them. Read-only import must pass before write access is even considered, and enabling writes requires separate owner approval. There is no current approval to enable them.

## Backup and restore

Use Settings to choose a backup directory outside `storage/`, save it, and request **Back up and verify restore**. Scheduled backups run only while the app is open; overdue scheduled work catches up once rather than duplicating every missed run. Each backup is restored and checked before being reported successful.

To inspect a restore into a **new** folder, from `apps/api`:

```sh
uv run python -m app.services.backup_cli restore \
  --archive /absolute/path/to/backup.zip \
  --destination /absolute/path/to/new-restore-folder
```

Substitute real local paths. This command checks archive contents/checksums and DB integrity and refuses to overwrite an existing destination. It does not switch the running app to that database. Stop all services and inspect the restored DB/files before any deliberate data switch. Keep the original data and encryption key intact; do not treat an untested laptop restore as complete just because cloud tests passed.

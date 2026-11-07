# Next step · Application tracker

A private, local-first workspace for UK graduate opportunities. The requirements are in [docs/SPEC.md](docs/SPEC.md); agents must also read [AGENTS.md](AGENTS.md).

## Current slice: Phase 1 foundation

Working: token-protected API, SQLite migrations, profile/fact CRUD and owner review, manual job intake with canonical-URL deduplication, job details/editing, shortlist/status history, dashboard, search, and in-app deadline reminders using the UK calendar. Data starts empty; no applicant details or sample jobs are seeded.

Not yet implemented: CV upload/parsing, URL extraction, sponsorship evidence editing, Google Sheets OAuth/import/sync, background worker, external reminder delivery, and automated backups. Phase 1 is **partial**. Later-phase preparation, matching and submission are not enabled.

## Local development

Requires Python 3.12+, uv, Node 24 and npm. Use the existing checkout; cloud tasks are already isolated, so do not create a worktree unless requested.

From the repository root:

```sh
python scripts/init_local.py
cd apps/api
uv sync --frozen
uv run alembic upgrade head
cd ../web
npm ci
cd ../..
python scripts/dev.py
```

API listens on loopback port 8000, UI on loopback port 3000. Open the local UI in your browser. Unlock it with `APP_ACCESS_TOKEN` from your private `.env` file, opened locally in your editor. The token is held in memory and cleared on refresh/lock. Never share or commit `.env`. The launcher loads `.env` values literally, without shell interpolation; exported environment variables take precedence. Restart after changing configuration. API refuses to start without a 32-character token or applied migrations.

Do not expose either port to the internet. Keep local browser, access-token file, DB and backups private. SQLite and profile facts are not encrypted; OAuth token encryption will be implemented before OAuth storage is added.

For separate processes, activate `apps/api/.venv`, export `APP_ACCESS_TOKEN` securely and run `uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log` from `apps/api`; run `npm run dev` from `apps/web`. The web server proxies only allowlisted API paths. It does not inject credentials: the browser must supply the token.

## Checks

```sh
cd apps/api
uv run pytest
uv run alembic check
cd ../web
npm run typecheck
npm run build
```

After building the frontend, run `uv run --frozen --group browser python ../../scripts/smoke_browser.py` from `apps/api`. The browser suite starts production services on loopback ports 8001/3001 and uses a disposable migrated database. It needs Chromium: set `CHROMIUM_EXECUTABLE`, use system `chromium`, or install Playwright Chromium with `uv run --group browser playwright install chromium`. Screenshots and service logs go to ignored `.local/`. It never uses the owner's database or access token.

Tests migrate isolated temporary databases and exercise authentication, CRUD, fact review invalidation, manual intake of ten unique URLs plus repeat dedupe, database constraints, status history, and migration rollback/reapply. These do **not** establish URL extraction or Google Sheets acceptance criteria. No real portals, live Sheet, or hosted model are contacted.

## Data and safety

`storage/` holds the local database and is gitignored. `application_events` has no update/delete API, and ORM updates/deletes are rejected. Database administrators can still change files directly. The API intentionally allows only foundation tracking statuses. `APPLIED`, approval and submission cannot be set, and confirmed sponsorship cannot be stored in this slice. Later phases must replace these restrictive constraints with evidence/approval checks through explicit migrations.

Only manually entered facts are stored. Editing a reviewed fact clears its review; confirm it again after checking the saved text. Sensitive legal declarations are not collected or inferred. Jobs and fact text render as escaped plain text.

For the next Phase 1 slices, provide tracker column headers and configure OAuth against a **copy** of the Sheet. Do not write to the real tracker. Choose an extraction provider/model before hosted extraction is enabled. Never send personal data to a hosted model without the owner's explicit confirmation of retention/training settings.

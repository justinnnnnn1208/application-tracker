"""Exercise the production UI against a migrated, disposable DB; never use owner data.

From apps/api: uv run --group browser python ../../scripts/smoke_browser.py
Requires apps/web to be built and Chromium installed (system Chromium is supported).
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps/api"


def wait_for(url, processes):
    for _ in range(120):
        if any(p.poll() is not None for p in processes):
            raise RuntimeError("A test service exited; inspect .local/browser-services.log")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.5)
    raise RuntimeError("Test service did not become ready")


def main():
    os.umask(0o077)
    (ROOT / ".local").mkdir(exist_ok=True)
    for port in (8001, 3001):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError(f"Test port {port} is already in use; stop its service first") from exc
    with tempfile.TemporaryDirectory(prefix="tracker-browser-") as temp, (ROOT / ".local/browser-services.log").open("w") as log:
        token = secrets.token_urlsafe(48)
        environment = {**os.environ, "APP_ACCESS_TOKEN": token, "DATABASE_URL": f"sqlite:///{temp}/test.db", "STORAGE_DIR": f"{temp}/storage", "API_BASE_URL": "http://127.0.0.1:8001", "NEXT_TELEMETRY_DISABLED": "1"}
        subprocess.run([str(API / ".venv/bin/alembic"), "upgrade", "head"], cwd=API, env=environment, check=True)
        processes = []
        try:
            processes.append(subprocess.Popen([str(API / ".venv/bin/uvicorn"), "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8001", "--no-access-log"], cwd=API, env=environment, stdout=log, stderr=log, start_new_session=True))
            processes.append(subprocess.Popen(["node", str(ROOT / "apps/web/node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", "3001"], cwd=ROOT / "apps/web", env=environment, stdout=log, stderr=log, start_new_session=True))
            processes.append(subprocess.Popen([str(API / ".venv/bin/python"), "-m", "app.worker.main"], cwd=API, env=environment, stdout=log, stderr=log, start_new_session=True))
            wait_for("http://127.0.0.1:8001/health", processes)
            wait_for("http://127.0.0.1:3001", processes)
            with sync_playwright() as playwright:
                executable = os.environ.get("CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                browser = playwright.chromium.launch(executable_path=executable, headless=True)
                context = browser.new_context(viewport={"width": 1440, "height": 1080})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                browser_api_headers = []
                page.on("request", lambda request: browser_api_headers.append(request.headers) if "/api/" in request.url else None)
                page.goto("http://127.0.0.1:3001")
                expect(page.get_by_role("button", name="Dashboard", exact=True)).to_have_attribute("aria-current", "page")
                expect(page.get_by_label("Job listing URL", exact=True)).to_be_visible()
                expect(page.get_by_label("Workspace access token")).to_have_count(0)
                expect(page.get_by_role("button", name="Lock workspace", exact=True)).to_have_count(0)
                assert context.request.get("http://127.0.0.1:3001/api/profile").status == 200
                # Direct backend access is still authenticated.
                assert context.request.get("http://127.0.0.1:8001/api/profile").status == 401
                # The proxy may use its server credential only for local, same-origin traffic.
                for headers in [
                    {"Origin": "https://untrusted.example.org"},
                    {"Origin": "http://127.0.0.1:3001", "Sec-Fetch-Site": "cross-site"},
                    {"Host": "untrusted.example.org", "Origin": "http://untrusted.example.org"},
                    {},
                ]:
                    assert context.request.post("http://127.0.0.1:3001/api/jobs", headers=headers, data={}).status == 403
                assert context.request.get("http://127.0.0.1:3001/api/profile", headers={"Sec-Fetch-Site": "cross-site"}).status == 403
                assert context.request.get("http://127.0.0.1:3001/api/profile", headers={"Host": "untrusted.example.org"}).status == 403
                page.reload()
                expect(page.get_by_label("Job listing URL", exact=True)).to_be_visible()
                page.get_by_role("button", name="Jobs", exact=True).click()
                page.get_by_role("button", name="Add a job", exact=False).first.click()
                page.get_by_label("Job URL").fill("https://example.org/fixture?utm_source=test")
                page.get_by_label("Company", exact=False).fill("Fixture employer")
                page.get_by_label("Role title").fill("Fixture graduate engineer")
                page.get_by_label("Location", exact=True).fill("Leeds")
                page.get_by_label("Application deadline").fill((datetime.now(ZoneInfo("Europe/London")).date() + timedelta(days=3)).isoformat())
                page.get_by_label("Job description").fill("Fixture job description. No sponsorship information supplied.")
                page.get_by_label("Your notes").fill("Fixture-only test record")
                with page.expect_response(lambda response: response.url.endswith("/api/jobs") and response.request.method == "POST") as saved:
                    page.get_by_role("button", name="Save opportunity").click()
                assert saved.value.status == 201, f"Job save failed: HTTP {saved.value.status}"
                page.get_by_role("button", name="Jobs", exact=True).click()
                page.screenshot(path=str(ROOT / ".local/browser-after-save.png"), full_page=True)
                page.get_by_role("button", name="View Fixture graduate engineer at Fixture employer").click()
                expect(page.get_by_role("heading", name="Fixture graduate engineer", exact=True)).to_be_visible()
                page.get_by_label("Update status").select_option("SHORTLISTED")
                expect(page.get_by_text("Discovered to Shortlisted", exact=True)).to_be_visible()
                page.get_by_role("button", name="Edit details").click()
                page.get_by_label("Your notes").fill("Updated fixture note")
                page.get_by_role("button", name="Save opportunity").click()
                expect(page.get_by_text("Updated fixture note", exact=True)).to_be_visible()
                page.get_by_role("button", name="My Profile", exact=True).click()
                page.get_by_label("Display name").fill("Fixture user")
                page.get_by_role("button", name="Save profile").click()
                expect(page.locator(".owner strong")).to_have_text("Fixture")
                page.get_by_label("Fact", exact=True).fill("Built a fixture project")
                page.get_by_label("Source", exact=True).fill("Fixture CV")
                page.get_by_role("button", name="Add fact for review").click()
                expect(page.get_by_text("Needs review", exact=True)).to_be_visible()
                page.get_by_role("button", name="I confirm this fact").click()
                expect(page.get_by_text("Reviewed", exact=True)).to_be_visible()
                page.get_by_role("button", name="Edit", exact=True).click()
                page.get_by_label("Fact", exact=True).last.fill("Changed fixture project")
                page.get_by_role("button", name="Save for review").click()
                expect(page.get_by_text("Needs review", exact=True)).to_be_visible()
                page.get_by_role("button", name="Deadlines", exact=True).click()
                expect(page.get_by_text("Fixture graduate engineer", exact=True)).to_be_visible()
                page.get_by_role("button", name="Jobs", exact=True).click()
                expect(page.get_by_role("table").get_by_text("Shortlisted", exact=True)).to_be_visible()
                # Extra disposable rows exercise combined filters and meaningful sorting.
                today = datetime.now(ZoneInfo("Europe/London")).date()
                for payload in [
                    {"url": "https://example.org/fixture-data", "company": "Another fixture employer", "title": "Fixture data analyst", "location": "London", "deadline": (today + timedelta(days=12)).isoformat(), "notes": "Find-this-note"},
                    {"url": "https://example.org/fixture-unknown", "company": "Z fixture employer", "title": "Fixture unknown deadline"},
                ]:
                    response = context.request.post("http://127.0.0.1:3001/api/jobs", headers={"Origin": "http://127.0.0.1:3001"}, data=payload)
                    assert response.status == 201
                page.reload()
                expect(page.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
                expect(page.locator(".stat").filter(has=page.get_by_text("Jobs tracked", exact=True)).locator("strong")).to_have_text("3")
                expect(page.locator(".stat").filter(has=page.get_by_text("Closing in 7 days", exact=True)).locator("strong")).to_have_text("1")
                expect(page.locator(".stat").filter(has=page.get_by_text("Applied", exact=True)).locator("strong")).to_have_text("0")
                expect(page.get_by_role("table").locator("tbody tr")).to_have_count(1)
                expect(page.get_by_text("Last Sheet sync:", exact=False)).to_be_visible()
                expect(page.get_by_role("button", name="Application Review", exact=True)).to_have_count(0)
                expect(page.get_by_role("columnheader", name="Match", exact=True)).to_have_count(0)
                page.screenshot(path=str(ROOT / ".local/dashboard-desktop.png"), full_page=True)
                page.get_by_role("button", name="Jobs", exact=True).click()
                rows = page.get_by_role("table").locator("tbody tr")
                expect(rows).to_have_count(3)
                page.get_by_label("Filter by status").select_option("SHORTLISTED")
                expect(rows).to_have_count(1)
                page.get_by_label("Filter by status").select_option("ALL")
                page.get_by_label("Filter by deadline").select_option("7")
                expect(rows).to_have_count(1)
                page.get_by_label("Filter by deadline").select_option("unknown")
                expect(rows).to_have_count(1)
                expect(rows.first).to_contain_text("Fixture unknown deadline")
                page.get_by_label("Filter by deadline").select_option("past")
                expect(page.get_by_role("heading", name="No jobs match these filters", exact=True)).to_be_visible()
                page.get_by_label("Filter by deadline").select_option("ALL")
                page.get_by_label("Search jobs").fill("Find-this-note")
                expect(rows).to_have_count(1)
                expect(rows.first).to_contain_text("Fixture data analyst")
                page.get_by_label("Search jobs").fill("")
                page.get_by_label("Filter by sponsorship").select_option("UNVERIFIED")
                expect(rows).to_have_count(3)
                page.get_by_label("Sort jobs").select_option("company")
                expect(rows.first).to_contain_text("Another fixture employer")
                page.get_by_label("Sort jobs").select_option("deadline")
                expect(rows.last).to_contain_text("Fixture unknown deadline")
                expect(page.locator(".unverified")).to_have_count(3)
                assert page.locator(".unverified").first.evaluate("e => getComputedStyle(e).backgroundColor") == "rgb(52, 55, 61)"
                page.screenshot(path=str(ROOT / ".local/browser-desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                expect(page.get_by_role("button", name="Lock workspace", exact=True)).to_have_count(0)
                for name in ["Dashboard", "Jobs", "Deadlines", "My Profile", "Settings"]:
                    expect(page.get_by_role("button", name=name, exact=True)).to_be_in_viewport()
                page.screenshot(path=str(ROOT / ".local/browser-mobile.png"), full_page=True)
                overflow = page.evaluate("""() => ({width: innerWidth, documentWidth: document.documentElement.scrollWidth,
                    elements: [...document.querySelectorAll('body *')].map(e => ({tag: e.tagName, cls: e.className,
                      right: Math.round(e.getBoundingClientRect().right), width: Math.round(e.getBoundingClientRect().width)}))
                      .filter(e => e.right > innerWidth + 1)})""")
                assert overflow["documentWidth"] <= overflow["width"], overflow
                # All Phase 1 pages must fit a mobile viewport; tables scroll internally.
                for name in ["Dashboard", "My Profile", "Settings", "Deadlines"]:
                    page.get_by_role("button", name=name, exact=True).click()
                    expect(page.get_by_role("heading", name=name, exact=True)).to_be_visible()
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), name
                page.get_by_role("button", name="Settings", exact=True).click()
                backups = page.locator("details").filter(has_text="Backup and restore").first
                expect(backups).to_have_attribute("open", "")
                backups.locator("summary").first.click()
                expect(backups).not_to_have_attribute("open", "")
                backups.locator("summary").first.click()
                expect(page.get_by_label("Backup destination folder")).to_be_visible()
                page.get_by_role("button", name="Dashboard", exact=True).click()
                page.set_viewport_size({"width": 320, "height": 800})
                expect(page.get_by_label("Job listing URL", exact=True)).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(ROOT / ".local/dashboard-mobile.png"), full_page=True)
                # Native controls remain usable without tiny touch targets.
                assert page.evaluate("""() => [...document.querySelectorAll('button,input,select,textarea,summary')].filter(e => {
                    const r = e.getBoundingClientRect(); return r.width && r.height && !e.disabled;
                  }).every(e => { const r = (e.type === 'checkbox' ? e.closest('label') : e).getBoundingClientRect(); return r.width >= 44 && r.height >= 44; })""")
                page.reload()
                expect(page.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
                expect(page.get_by_label("Workspace access token")).to_have_count(0)
                assert token not in page.content()
                assert browser_api_headers and all("authorization" not in headers for headers in browser_api_headers)
                assert page.evaluate("localStorage.length === 0 && sessionStorage.length === 0")
                assert context.cookies() == []
                # Closing and reopening a browser context must also skip the unlock page.
                context.close()
                fresh = browser.new_context()
                reopened = fresh.new_page()
                reopened.goto("http://127.0.0.1:3001")
                expect(reopened.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
                expect(reopened.get_by_label("Workspace access token")).to_have_count(0)
                fresh.close()
                # Restarting the local web server also needs no browser login.
                os.killpg(processes[1].pid, signal.SIGTERM)
                processes[1].wait(timeout=5)
                processes[1] = subprocess.Popen(["node", str(ROOT / "apps/web/node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", "3001"], cwd=ROOT / "apps/web", env=environment, stdout=log, stderr=log, start_new_session=True)
                wait_for("http://127.0.0.1:3001", processes)
                restarted = browser.new_page()
                restarted.add_init_script("""window.fixtureNotifications = []; window.fixturePermissionRequests = 0;
                    window.Notification = class {
                      static permission = 'default';
                      static async requestPermission() { window.fixturePermissionRequests++; this.permission = 'granted'; return 'granted'; }
                      constructor(title, options) { window.fixtureNotifications.push({title, ...options}); }
                      close() {}
                    };""")
                restarted.goto("http://127.0.0.1:3001")
                expect(restarted.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
                expect(restarted.get_by_label("Workspace access token")).to_have_count(0)
                assert restarted.evaluate("fixtureNotifications.length === 0 && fixturePermissionRequests === 0")
                restarted.get_by_role("button", name="Enable desktop reminders", exact=True).click()
                expect(restarted.get_by_role("button", name="Pause desktop reminders", exact=True)).to_be_visible()
                restarted.wait_for_function("fixtureNotifications.length === 1")
                assert restarted.evaluate("fixtureNotifications[0].body.includes('Fixture graduate engineer')")
                restarted.get_by_role("button", name="Pause desktop reminders", exact=True).click()
                restarted.get_by_role("button", name="Enable desktop reminders", exact=True).click()
                assert restarted.evaluate("fixtureNotifications.length === 1")
                # Exercise the actual separate worker, using pasted fixture HTML only.
                restarted.get_by_label("Job listing URL", exact=True).fill("https://example.org/worker-browser")
                restarted.get_by_text("Paste page HTML instead", exact=True).click()
                listing = {"@context": "https://schema.org", "@type": "JobPosting", "title": "Browser worker engineer", "hiringOrganization": {"name": "Worker fixture company"}, "description": "Fixture description", "jobLocation": {"address": {"addressLocality": "Leeds"}}}
                restarted.get_by_label("Public job page HTML").fill('<script type="application/ld+json">' + json.dumps(listing) + '</script>')
                restarted.get_by_role("button", name="Add job", exact=True).click()
                restarted.get_by_text("Background tasks", exact=False).first.click()
                expect(restarted.locator(".task-row").filter(has_text="Job URL extraction").get_by_text("succeeded", exact=True)).to_be_visible(timeout=20000)
                restarted.get_by_role("button", name="Jobs", exact=True).click()
                expect(restarted.get_by_role("table")).to_contain_text("Browser worker engineer")
                restarted.get_by_role("button", name="My Profile", exact=True).click()
                cv_bytes = b"Skills\nPython fixture browser skill\n"
                restarted.get_by_label("CV file", exact=True).set_input_files({"name": "fixture.txt", "mimeType": "text/plain", "buffer": cv_bytes})
                restarted.get_by_role("button", name="Upload CV for local parsing", exact=True).click()
                candidate = restarted.get_by_role("textbox", name="Candidate fact")
                expect(candidate).to_have_value("Python fixture browser skill", timeout=20000)
                expect(restarted.get_by_role("button", name="Save confirmed fact")).to_be_disabled()
                candidate.fill("Python fixture browser skill reviewed")
                restarted.get_by_role("combobox", name="Candidate category").select_option("skill")
                restarted.get_by_label("I have checked and confirm this exact fact.", exact=True).check()
                restarted.get_by_role("button", name="Save confirmed fact", exact=True).click()
                expect(candidate).to_have_count(0)
                expect(restarted.get_by_text("Python fixture browser skill reviewed", exact=True)).to_be_visible()
                with restarted.expect_download() as downloaded:
                    restarted.get_by_role("button", name="Download CV", exact=False).click()
                assert Path(downloaded.value.path()).read_bytes() == cv_bytes
                restarted.get_by_role("button", name="Settings", exact=True).click()
                restarted.get_by_label("Backup destination folder", exact=True).fill(str(Path(temp) / "backups"))
                restarted.get_by_role("button", name="Save settings", exact=True).click()
                expect(restarted.get_by_text("Settings saved.", exact=True)).to_be_visible()
                restarted.get_by_role("button", name="Back up and verify restore", exact=True).click()
                task_panel = restarted.locator("details.task-panel")
                if not task_panel.get_attribute("open"):
                    task_panel.locator("summary").click()
                expect(task_panel.get_by_text("Backup restored and verified.", exact=False).first).to_be_visible(timeout=20000)
                archives = sorted((Path(temp) / "backups").glob("*.zip"))
                assert archives
                destination = Path(temp) / "restored"
                subprocess.run([str(API / ".venv/bin/python"), "-m", "app.services.backup_cli", "restore", "--archive", str(archives[-1]), "--destination", str(destination)], cwd=API, env=environment, check=True, stdout=log, stderr=log)
                with sqlite3.connect(destination / "database.sqlite3") as restored:
                    assert restored.execute("SELECT count(*) FROM jobs").fetchone()[0] == 4
                    assert restored.execute("SELECT count(*) FROM facts WHERE content = ?", ("Python fixture browser skill reviewed",)).fetchone()[0] == 1
                assert any(path.read_bytes() == cv_bytes for path in (destination / "storage").rglob("*") if path.is_file())
                assert not errors, errors
                browser.close()
                print("Browser smoke passed: direct dashboard on initial load/reload/new browser/server restart, server-only credential, local origin guards, backend authentication, job CRUD/history, profile/fact review, deadlines, filters/sorting, native disclosures, real-worker HTML extraction, CV upload/review/download, UI backup plus CLI restore, opt-in desktop reminders with session dedupe, charcoal theme and 1440/390/320px layouts. Disposable data removed.")
        finally:
            for process in processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
            for process in processes:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


if __name__ == "__main__":
    main()

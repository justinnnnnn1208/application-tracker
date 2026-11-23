"""Exercise the production UI against a migrated, disposable DB; never use owner data.

From apps/api: uv run --group browser python ../../scripts/smoke_browser.py
Requires apps/web to be built and Chromium installed (system Chromium is supported).
"""
import os
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import json
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import secrets
import shutil
import signal
import socket
import sys
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps/api"
sys.path.insert(0, str(API))


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


@contextmanager
def ollama_fixture():
    """Synthetic local HTTP contract only; never claim this is real model evaluation."""
    captured = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path == '/api/show':
                assert body == {'model': 'fixture-contract-only'}
                data = json.dumps({'model_info': {'general.architecture': 'fixture'}}).encode()
            else:
                assert self.path == '/api/chat' and 'tools' not in body
                captured.append(body)
                text = body['messages'][-1]['content']
                assert 'Updated fixture note' not in text and 'Fixture-only test record' not in text
                skills = [{'value': 'Elixir', 'quote': 'Elixir required.'}] if 'Elixir required.' in text else []
                data = json.dumps({'done': True, 'done_reason': 'stop', 'message': {'content': json.dumps({'skills': skills, 'education': [], 'experience': []})}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True);thread.start()
    try:
        yield server.server_port, captured
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)


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
    with ollama_fixture() as (model_port, model_calls), tempfile.TemporaryDirectory(prefix="tracker-browser-") as temp, (ROOT / ".local/browser-services.log").open("w") as log:
        token = secrets.token_urlsafe(48)
        environment = {**os.environ, "APP_ACCESS_TOKEN": token, "DATABASE_URL": f"sqlite:///{temp}/test.db", "STORAGE_DIR": f"{temp}/storage", "API_BASE_URL": "http://127.0.0.1:8001", "NEXT_TELEMETRY_DISABLED": "1", "REED_API_KEY": "", "LLM_PROVIDER": "ollama", "LLM_MODEL": "fixture-contract-only", "LLM_BASE_URL": f"http://127.0.0.1:{model_port}/v1"}
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
                page.get_by_label("Job description").fill("Fixture job description. Elixir required. We offer visa sponsorship for this role.")
                page.get_by_label("Your notes").fill("Fixture-only test record")
                with page.expect_response(lambda response: response.url.endswith("/api/jobs") and response.request.method == "POST") as saved:
                    page.get_by_role("button", name="Save opportunity").click()
                assert saved.value.status == 201, f"Job save failed: HTTP {saved.value.status}"
                page.get_by_role("button", name="Jobs", exact=True).click()
                page.screenshot(path=str(ROOT / ".local/browser-after-save.png"), full_page=True)
                page.get_by_role("button", name="View Fixture graduate engineer at Fixture employer").click()
                expect(page.get_by_role("heading", name="Fixture graduate engineer", exact=True)).to_be_visible()
                page.get_by_role("button", name="Calculate preference match", exact=True).click()
                expect(page.get_by_text("/100", exact=False)).to_be_visible(timeout=20000)
                page.get_by_role("button", name="Good match", exact=True).click()
                expect(page.get_by_text("Rating saved: good.", exact=False)).to_be_visible()
                page.get_by_text("Why this score?", exact=True).click()
                expect(page.get_by_text("Explicit graduate/junior/new-grad/early-career title.", exact=True)).to_be_visible()
                page.get_by_label("Update status").select_option("SHORTLISTED")
                expect(page.get_by_text("Discovered to Shortlisted", exact=True)).to_be_visible()
                page.get_by_role("button", name="Edit details").click()
                page.get_by_label("Your notes").fill("Updated fixture note")
                page.get_by_role("button", name="Save opportunity").click()
                expect(page.get_by_text("Updated fixture note", exact=True)).to_be_visible()
                source_requirements = page.get_by_role("region", name="Source requirements", exact=True)
                source_requirements.get_by_role("button", name="Extract requirements locally", exact=True).click()
                source_requirements.get_by_text("View extracted terms and quotes", exact=True).click(timeout=20000)
                expect(source_requirements.get_by_text("Elixir", exact=True)).to_be_visible()
                expect(source_requirements.get_by_text("Elixir required.", exact=True)).to_be_visible()
                expect(page.get_by_text("Job, reviewed facts or preferences changed.", exact=False)).to_be_visible()
                page.get_by_role("button", name="Calculate preference match", exact=True).click()
                expect(page.get_by_text("/100", exact=False)).to_be_visible(timeout=20000)
                assert len(model_calls) == 1
                # Only the owner review, not the source wording, establishes a finding.
                sponsorship_panel = page.get_by_role("region", name="Sponsorship evidence")
                expect(sponsorship_panel.get_by_text("Unverified", exact=True)).to_be_visible()
                sponsorship_panel.get_by_text("Review role-specific evidence", exact=True).click()
                sponsorship_panel.get_by_label("Sponsorship finding", exact=True).select_option("CONFIRMED_YES")
                sponsorship_panel.get_by_label("Exact sponsorship quote", exact=True).fill("We offer visa sponsorship for this role.")
                source_option = sponsorship_panel.get_by_label("Evidence listing source", exact=True).locator("option").nth(1).get_attribute("value")
                sponsorship_panel.get_by_label("Evidence listing source", exact=True).select_option(source_option)
                expect(sponsorship_panel.get_by_role("button", name="Save sponsorship evidence", exact=True)).to_be_disabled()
                sponsorship_panel.get_by_role("checkbox").check()
                sponsorship_panel.get_by_role("button", name="Save sponsorship evidence", exact=True).click()
                expect(sponsorship_panel.get_by_text("Confirmed", exact=True)).to_be_visible()
                expect(sponsorship_panel.get_by_role("link", name="Open evidence source")).to_have_attribute("href", source_option)
                expect(sponsorship_panel.get_by_text("Evidence review saved.", exact=True)).to_be_visible()
                sponsorship_panel.get_by_role("button", name="Clear sponsorship review", exact=True).click()
                expect(sponsorship_panel.get_by_text("Unverified", exact=True)).to_be_visible()
                expect(sponsorship_panel.get_by_text("Evidence review saved.", exact=True)).to_have_count(0)
                expect(sponsorship_panel.get_by_role("checkbox")).not_to_be_checked()
                sponsorship_panel.get_by_role("checkbox").check()
                sponsorship_panel.get_by_role("button", name="Save sponsorship evidence", exact=True).click()
                expect(sponsorship_panel.get_by_text("Confirmed", exact=True)).to_be_visible()
                page.get_by_role("button", name="Back to opportunities", exact=True).click()
                page.get_by_label("Filter by sponsorship").select_option("CONFIRMED_YES")
                expect(page.get_by_role("table").locator("tbody tr")).to_have_count(1)
                page.get_by_role("button", name="Confirmed · Evidence", exact=True).click()
                page.get_by_role("button", name="Edit details", exact=True).click()
                page.get_by_label("Job description").fill("Fixture job description. Sponsorship policy has changed.")
                page.get_by_role("button", name="Save opportunity", exact=True).click()
                sponsorship_panel = page.get_by_role("region", name="Sponsorship evidence")
                expect(sponsorship_panel.get_by_text("Vacancy content changed.", exact=False)).to_be_visible()
                expect(sponsorship_panel.get_by_text("Unverified", exact=True)).to_be_visible()
                sponsorship_panel.get_by_role("button", name="Clear sponsorship review", exact=True).click()
                expect(sponsorship_panel.get_by_role("link", name="Open evidence source")).to_have_count(0)
                expect(sponsorship_panel.get_by_text("Evidence review saved.", exact=True)).to_have_count(0)
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
                expect(page.get_by_role("link", name="Open job listing at Fixture employer", exact=True)).to_have_attribute("href", "https://example.org/fixture")
                expect(page.get_by_role("link", name="Open job listing at Fixture employer", exact=True)).to_have_attribute("rel", "noopener noreferrer")
                expect(page.locator(".unverified")).to_have_count(3)
                assert page.locator(".unverified").first.evaluate("e => getComputedStyle(e).backgroundColor") == "rgb(52, 55, 61)"
                # Simulated imported history stays separate from confirmed application state.
                with sqlite3.connect(Path(temp) / "test.db") as fixture_db:
                    fixture_db.execute("UPDATE jobs SET tracker_status = 'Applied' WHERE url = ?", ("https://example.org/fixture-unknown",))
                page.reload()
                expect(page.locator(".stat").filter(has=page.get_by_text("Applied", exact=True)).locator("strong")).to_have_text("0")
                expect(page.get_by_text("1 applied in Sheet · no stored confirmation", exact=True)).to_be_visible()
                page.get_by_role("button", name="Jobs", exact=True).click()
                page.get_by_label("Filter by status").select_option("IMPORTED_APPLIED")
                expect(page.get_by_role("table").locator("tbody tr")).to_have_count(1)
                expect(page.get_by_role("table").get_by_text("Applied — imported from Sheet", exact=True)).to_be_visible()
                page.get_by_label("Filter by status").select_option("ALL")
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
                preferences_panel = page.locator("details").filter(has=page.locator("summary", has_text="Matching preferences")).first
                preferences_panel.locator("summary").click()
                preferences_panel.get_by_label("Role preference weight", exact=True).fill("30")
                expect(preferences_panel.get_by_role("button", name="Save matching preferences", exact=True)).to_be_disabled()
                preferences_panel.get_by_label("Graduate/junior level weight", exact=True).fill("15")
                preferences_panel.get_by_label("Preferred role keywords", exact=True).fill("software engineer, data")
                preferences_panel.get_by_role("button", name="Save matching preferences", exact=True).click()
                expect(preferences_panel.get_by_text("Matching preferences saved.", exact=False)).to_be_visible()
                page.reload()
                page.get_by_role("button", name="Settings", exact=True).click()
                preferences_panel = page.locator("details").filter(has=page.locator("summary", has_text="Matching preferences")).first
                preferences_panel.locator("summary").click()
                expect(preferences_panel.get_by_label("Role preference weight", exact=True)).to_have_value("30")
                expect(preferences_panel.get_by_label("Graduate/junior level weight", exact=True)).to_have_value("15")
                expect(preferences_panel.get_by_label("Preferred role keywords", exact=True)).to_have_value("software engineer, data")
                preferences_panel.locator("summary").click()
                discovery = page.locator("details").filter(has=page.locator("summary", has_text="Job discovery")).first
                discovery.locator("summary").click()
                discovery.get_by_label("Greenhouse board slug", exact=True).fill("fixture-board")
                discovery.get_by_role("button", name="Add discovery source", exact=True).click()
                expect(discovery.get_by_role("button", name="Discover jobs from fixture-board", exact=True)).to_be_disabled()
                discovery.get_by_role("button", name="Remove fixture-board", exact=True).click()
                expect(discovery.get_by_role("button", name="Remove fixture-board", exact=True)).to_have_count(0)
                discovery.get_by_label("Discovery provider", exact=True).select_option("lever")
                discovery.get_by_label("Lever board slug", exact=True).fill("fixture-lever")
                discovery.get_by_label("Employer name on the board", exact=True).fill("Fixture Lever Employer")
                discovery.get_by_label("Lever region", exact=True).select_option("eu")
                discovery.get_by_role("button", name="Add discovery source", exact=True).click()
                expect(discovery.get_by_text("Fixture Lever Employer", exact=True)).to_be_visible()
                expect(discovery.get_by_text("Lever · EU · fixture-lever", exact=True)).to_be_visible()
                expect(discovery.get_by_role("button", name="Discover jobs from fixture-lever", exact=True)).to_be_disabled()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                discovery.get_by_role("button", name="Remove fixture-lever", exact=True).click()
                expect(discovery.get_by_role("button", name="Remove fixture-lever", exact=True)).to_have_count(0)
                discovery.get_by_label("Discovery provider", exact=True).select_option("ashby")
                discovery.get_by_label("Ashby board slug", exact=True).fill("fixture-ashby")
                discovery.get_by_label("Employer name on the board", exact=True).fill("Fixture Ashby Employer")
                expect(discovery.get_by_label("Lever region", exact=True)).to_have_count(0)
                discovery.get_by_role("button", name="Add discovery source", exact=True).click()
                expect(discovery.get_by_text("Ashby · fixture-ashby", exact=True)).to_be_visible()
                expect(discovery.get_by_role("button", name="Discover jobs from fixture-ashby", exact=True)).to_be_disabled()
                discovery.get_by_role("button", name="Remove fixture-ashby", exact=True).click()
                expect(discovery.get_by_role("button", name="Remove fixture-ashby", exact=True)).to_have_count(0)
                discovery.get_by_label("Discovery provider", exact=True).select_option("smartrecruiters")
                discovery.get_by_label("SmartRecruiters company identifier", exact=True).fill("FixtureCompany")
                discovery.get_by_label("Employer name on the board", exact=True).fill("Fixture SmartRecruiters Employer")
                discovery.get_by_role("button", name="Add discovery source", exact=True).click()
                expect(discovery.get_by_text("SmartRecruiters · FixtureCompany", exact=True)).to_be_visible()
                expect(discovery.get_by_role("button", name="Discover jobs from FixtureCompany", exact=True)).to_be_disabled()
                discovery.get_by_role("button", name="Remove FixtureCompany", exact=True).click()
                expect(discovery.get_by_role("button", name="Remove FixtureCompany", exact=True)).to_have_count(0)
                discovery.get_by_label("Discovery provider", exact=True).select_option("reed")
                discovery.get_by_label("Reed search keywords", exact=True).fill("graduate software")
                expect(discovery.get_by_label("Employer name on the board", exact=True)).to_have_count(0)
                discovery.get_by_role("button", name="Add discovery source", exact=True).click()
                expect(discovery.get_by_text("Private Reed API key not configured.", exact=True)).to_be_visible()
                expect(discovery.get_by_role("button", name="Discover jobs from graduate software", exact=True)).to_be_disabled()
                assert 'fixture-private-api-key' not in page.content()
                discovery.get_by_role("button", name="Remove graduate software", exact=True).click()
                expect(discovery.get_by_role("button", name="Remove graduate software", exact=True)).to_have_count(0)
                discovery.locator("summary").click()
                register_panel = page.locator("details").filter(has=page.locator("summary", has_text="Sponsor register")).first
                register_panel.locator("summary").first.click()
                register_csv = b"Organisation Name,Town/City,Route\nFixture employer,Leeds,Skilled Worker\n"
                register_panel.get_by_label("Sponsor register CSV", exact=True).set_input_files({"name":"fixture-register.csv","mimeType":"text/csv","buffer":register_csv})
                register_panel.get_by_label("Official register CSV URL", exact=True).fill("https://assets.publishing.service.gov.uk/media/fixture/register.csv")
                register_panel.get_by_label("Register publication date", exact=True).fill(today.isoformat())
                expect(register_panel.get_by_role("button", name="Import sponsor register", exact=True)).to_be_disabled()
                register_panel.get_by_role("checkbox").check()
                register_panel.get_by_role("button", name="Import sponsor register", exact=True).click()
                expect(register_panel.get_by_text("Current file:", exact=False)).to_be_visible(timeout=20000)
                page.get_by_role("button", name="Jobs", exact=True).click()
                page.get_by_role("button", name="View Fixture graduate engineer at Fixture employer", exact=True).click()
                register_signal = page.get_by_role("region", name="Sponsor register signal", exact=True)
                expect(register_signal.get_by_text("Exact name found in imported register", exact=True)).to_be_visible()
                expect(register_signal.get_by_text("Routes: Skilled Worker", exact=True)).to_be_visible()
                expect(page.get_by_role("region", name="Sponsorship evidence").get_by_text("Unverified", exact=True)).to_be_visible()
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
                # An alternate official ATS URL must retain one job and expose both sources.
                base = "http://127.0.0.1:3001/api"
                fixture_job = next(job for job in restarted.request.get(base + "/jobs").json() if job["url"] == "https://example.org/worker-browser")
                original_data = {key: fixture_job[key] for key in ["url", "company", "title", "location", "description", "deadline", "start_date", "eligibility_requirements", "notes"]}
                ats_data = {**original_data, "url": "https://job-boards.greenhouse.io/fixture/jobs/456"}
                origin = {"Origin": "http://127.0.0.1:3001"}
                assert restarted.request.put(base + f"/jobs/{fixture_job['id']}", headers=origin, data=ats_data).status == 200
                alias = {**ats_data, "url": "https://boards.greenhouse.io/fixture/jobs/456"}
                repeated = restarted.request.post(base + "/jobs", headers=origin, data=alias)
                assert repeated.status == 200 and repeated.json()["id"] == fixture_job["id"]
                assert len(restarted.request.get(base + "/jobs").json()) == 4
                assert restarted.request.put(base + f"/jobs/{fixture_job['id']}", headers=origin, data=original_data).status == 200
                restarted.get_by_role("button", name="View Browser worker engineer at Worker fixture company", exact=True).click()
                expect(restarted.get_by_role("heading", name="Sources and possible duplicates", exact=True)).to_be_visible()
                expect(restarted.get_by_role("link", name="https://boards.greenhouse.io/fixture/jobs/456", exact=True)).to_have_attribute("rel", "noopener noreferrer")
                # Reviewed cross-source URLs reuse one application; undo removes only the link.
                source_panel = restarted.get_by_role("heading", name="Sources and possible duplicates", exact=True).locator("..")
                history_before = restarted.request.get(base + f"/jobs/{fixture_job['id']}/events").json()
                source_panel.get_by_text("Link another listing for this vacancy", exact=True).click()
                secondary = "https://example.org/reviewed-secondary"
                source_panel.get_by_label("Additional listing URL", exact=True).fill(secondary)
                expect(source_panel.get_by_role("button", name="Link reviewed listing", exact=True)).to_be_disabled()
                source_panel.get_by_role("checkbox").check()
                source_panel.get_by_role("button", name="Link reviewed listing", exact=True).click()
                expect(source_panel.get_by_role("link", name=secondary, exact=True)).to_be_visible()
                assert restarted.request.post(base + "/jobs", headers=origin, data={**original_data, "url": secondary}).json()["id"] == fixture_job["id"]
                assert len(restarted.request.get(base + "/jobs").json()) == 4
                restarted.once("dialog", lambda dialog: dialog.accept())
                source_panel.get_by_role("button", name="Remove reviewed link", exact=True).click()
                expect(source_panel.get_by_role("link", name=secondary, exact=True)).to_have_count(0)
                expect(source_panel.get_by_text("Secondary link removed. Job and history retained.", exact=True)).to_be_visible()
                assert restarted.request.get(base + f"/jobs/{fixture_job['id']}/events").json() == history_before
                assert len(restarted.request.get(base + "/jobs").json()) == 4
                restarted.get_by_role("button", name="Jobs", exact=True).click()
                # Simulate an earlier Sheet import and verify automatic repair on API restart.
                from sqlalchemy import select
                from sqlalchemy.orm import Session
                from app.db.models import Job, SheetLink
                from app.db.session import make_engine
                notes = "Graduate Software Engineer, Leeds. Python relevant; sponsorship not confirmed."
                fixture_engine = make_engine(environment["DATABASE_URL"])
                with Session(fixture_engine) as session:
                    imported = session.scalar(select(Job).where(Job.url == "https://example.org/worker-browser"))
                    imported.title, imported.description, imported.location, imported.notes = "Role not provided", "", "", notes
                    session.add(SheetLink(spreadsheet_id="fixture-development-copy", tab="Tracker", row_number=2, job_id=imported.id, row_hash="fixture", raw_values=[], raw_formulas=[], last_db_values={}))
                    session.commit()
                fixture_engine.dispose()
                os.killpg(processes[0].pid, signal.SIGTERM)
                processes[0].wait(timeout=5)
                processes[0] = subprocess.Popen([str(API / ".venv/bin/uvicorn"), "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8001", "--no-access-log"], cwd=API, env=environment, stdout=log, stderr=log, start_new_session=True)
                wait_for("http://127.0.0.1:8001/health", processes)
                restarted.reload()
                restarted.get_by_role("button", name="Jobs", exact=True).click()
                restarted.get_by_role("button", name="View Graduate Software Engineer, Leeds at Worker fixture company", exact=True).click()
                expect(restarted.get_by_role("heading", name="Description from Notes", exact=True)).to_be_visible()
                expect(restarted.get_by_text(notes, exact=True)).to_have_count(1)
                expect(restarted.get_by_text("Based on your Notes summary.", exact=False)).to_be_visible()
                restarted.get_by_role("button", name="Jobs", exact=True).click()
                restarted.get_by_role("button", name="Score active jobs", exact=True).click()
                note_row = restarted.get_by_role("table").locator("tbody tr").filter(has_text="Worker fixture company")
                expect(note_row).to_contain_text("/100", timeout=20000)
                restarted.get_by_label("Sort jobs").select_option("match")
                expect(restarted.get_by_role("table").locator("tbody tr").first).to_contain_text("Worker fixture company")
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
                    assert restored.execute("SELECT organisations FROM sponsor_register").fetchone()[0] == 1
                    assert restored.execute("SELECT name FROM sponsor_organisations").fetchone()[0] == "Fixture employer"
                    assert restored.execute("SELECT count(*) FROM facts WHERE content = ?", ("Python fixture browser skill reviewed",)).fetchone()[0] == 1
                assert any(path.read_bytes() == cv_bytes for path in (destination / "storage").rglob("*") if path.is_file())
                assert any(path.read_bytes() == register_csv for path in (destination / "storage/registers").glob("*.csv"))
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

"""Exercise the production UI against a migrated, disposable DB; never use owner data.

From apps/api: uv run --group browser python ../../scripts/smoke_browser.py
Requires apps/web to be built and Chromium installed (system Chromium is supported).
"""
import os
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
        environment = {**os.environ, "APP_ACCESS_TOKEN": token, "DATABASE_URL": f"sqlite:///{temp}/test.db", "API_BASE_URL": "http://127.0.0.1:8001", "NEXT_TELEMETRY_DISABLED": "1"}
        subprocess.run([str(API / ".venv/bin/alembic"), "upgrade", "head"], cwd=API, env=environment, check=True)
        processes = []
        try:
            processes.append(subprocess.Popen([str(API / ".venv/bin/uvicorn"), "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8001", "--no-access-log"], cwd=API, env=environment, stdout=log, stderr=log, start_new_session=True))
            processes.append(subprocess.Popen(["node", str(ROOT / "apps/web/node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", "3001"], cwd=ROOT / "apps/web", env=environment, stdout=log, stderr=log, start_new_session=True))
            wait_for("http://127.0.0.1:8001/health", processes)
            wait_for("http://127.0.0.1:3001", processes)
            with sync_playwright() as playwright:
                executable = os.environ.get("CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                browser = playwright.chromium.launch(executable_path=executable, headless=True)
                context = browser.new_context(viewport={"width": 1440, "height": 1080})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto("http://127.0.0.1:3001")
                expect(page.get_by_role("heading", name="Welcome back.")).to_be_visible()
                assert context.request.get("http://127.0.0.1:3001/api/profile").status == 401
                rejected = context.request.post("http://127.0.0.1:3001/api/jobs", headers={"Authorization": f"Bearer {token}", "Origin": "https://untrusted.example.org"}, data={})
                assert rejected.status == 403
                page.get_by_label("Workspace access token").fill(token)
                page.get_by_role("button", name="Unlock workspace").click()
                expect(page.get_by_role("heading", name="Your next opportunity goes here.")).to_be_visible()
                page.get_by_role("button", name="Add a job", exact=False).first.click()
                page.get_by_label("Job URL").fill("https://example.org/fixture?utm_source=test")
                page.get_by_label("Company", exact=False).fill("Fixture employer")
                page.get_by_label("Role title").fill("Fixture graduate engineer")
                page.get_by_label("Location", exact=True).fill("Leeds")
                page.get_by_label("Application deadline").fill("2027-01-15")
                page.get_by_label("Job description").fill("Fixture job description. No sponsorship information supplied.")
                page.get_by_label("Your notes").fill("Fixture-only test record")
                with page.expect_response(lambda response: response.url.endswith("/api/jobs") and response.request.method == "POST") as saved:
                    page.get_by_role("button", name="Save opportunity").click()
                assert saved.value.status == 201, f"Job save failed: HTTP {saved.value.status}"
                page.screenshot(path=str(ROOT / ".local/browser-after-save.png"), full_page=True)
                page.get_by_role("button", name="View Fixture graduate engineer at Fixture employer").click()
                expect(page.get_by_role("heading", name="Fixture graduate engineer", exact=True)).to_be_visible()
                page.get_by_label("Update status").select_option("SHORTLISTED")
                expect(page.get_by_text("Discovered to Shortlisted", exact=True)).to_be_visible()
                page.get_by_role("button", name="Edit details").click()
                page.get_by_label("Your notes").fill("Updated fixture note")
                page.get_by_role("button", name="Save opportunity").click()
                expect(page.get_by_text("Updated fixture note", exact=True)).to_be_visible()
                page.get_by_role("button", name="Profile & facts", exact=True).click()
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
                page.get_by_role("button", name="Overview", exact=True).click()
                expect(page.get_by_role("table").get_by_text("Shortlisted", exact=True)).to_be_visible()
                page.screenshot(path=str(ROOT / ".local/browser-desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                expect(page.get_by_role("button", name="Lock workspace", exact=True)).to_be_visible()
                page.screenshot(path=str(ROOT / ".local/browser-mobile.png"), full_page=True)
                overflow = page.evaluate("""() => ({width: innerWidth, documentWidth: document.documentElement.scrollWidth,
                    elements: [...document.querySelectorAll('body *')].map(e => ({tag: e.tagName, cls: e.className,
                      right: Math.round(e.getBoundingClientRect().right), width: Math.round(e.getBoundingClientRect().width)}))
                      .filter(e => e.right > innerWidth + 1)})""")
                assert overflow["documentWidth"] <= overflow["width"], overflow
                page.get_by_role("button", name="Lock workspace", exact=True).click()
                expect(page.get_by_role("heading", name="Welcome back.")).to_be_visible()
                page.get_by_label("Workspace access token").fill(token)
                page.get_by_role("button", name="Unlock workspace").click()
                expect(page.get_by_role("heading", name="Let’s make your next move, Fixture.")).to_be_visible()
                page.reload()
                expect(page.get_by_role("heading", name="Welcome back.")).to_be_visible()
                assert not errors, errors
                browser.close()
                print("Browser smoke passed: authentication, job create/edit/status/history, profile, fact review invalidation, deadlines, desktop/mobile layout, lock/reload. Disposable data removed.")
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

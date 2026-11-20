"""Run the local app or check its configured model against public fixtures."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--migrate", action="store_true", help="Back up/verify existing SQLite data, apply migrations, then start")
    mode.add_argument("--check-model", action="store_true", help="Check the configured local model against public fixtures; do not start the app")
    args = parser.parse_args()
    os.umask(0o077)
    environment = os.environ.copy()
    environment.setdefault("NEXT_TELEMETRY_DISABLED", "1")
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                environment.setdefault(key.strip(), value.strip())
    if args.check_model:
        interpreter = ROOT / "apps/api/.venv/bin/python"
        if not interpreter.is_file():
            print("Install API dependencies first: run uv sync --frozen from apps/api, then return to the project root.")
            return 2
        report = ROOT / ".local" / f"requirements-check-{uuid4().hex}.json"
        # This public-data check needs only model selectors, never app/OAuth/API
        # credentials, database settings or an inherited Python module path.
        public_environment = {"PATH": environment.get("PATH", os.defpath), "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1"}
        public_environment.update({key: environment[key] for key in ("LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL") if key in environment})
        result = subprocess.run([str(interpreter), "-m", "app.services.requirements_eval",
                                 "--manifest", str(ROOT / "fixtures/eval/manifest-nov20.json"),
                                 "--review", str(ROOT / "fixtures/eval/requirements-review.json"),
                                 "--output", str(report)], cwd=ROOT / "apps/api", env=public_environment)
        if report.is_file():
            print(f"Public model-check report: {report.relative_to(ROOT)}", flush=True)
        return result.returncode
    if len(environment.get("APP_ACCESS_TOKEN", "")) < 32:
        sys.exit("Run python scripts/init_local.py or configure APP_ACCESS_TOKEN (32+ characters).")
    if args.migrate:
        migration = subprocess.run([str(ROOT / "apps/api/.venv/bin/python"), "-m", "app.services.migration_cli"], cwd=ROOT / "apps/api", env=environment)
        if migration.returncode:
            return migration.returncode
    commands = [
        ([str(ROOT / "apps/api/.venv/bin/uvicorn"), "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000", "--no-access-log"], ROOT / "apps/api"),
        ([str(ROOT / "apps/api/.venv/bin/python"), "-m", "app.worker.main"], ROOT / "apps/api"),
        (["npm", "run", "dev"], ROOT / "apps/web"),
    ]
    processes = []

    def stop(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        for command, directory in commands:
            processes.append(subprocess.Popen(command, cwd=directory, env=environment, start_new_session=True))
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        return next((process.returncode for process in processes if process.returncode is not None), 1) or 1
    except KeyboardInterrupt:
        return 0
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
    sys.exit(main())

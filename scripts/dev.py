"""Run localhost API and UI together; terminate both on Ctrl+C or child failure."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.umask(0o077)
    environment = os.environ.copy()
    environment.setdefault("NEXT_TELEMETRY_DISABLED", "1")
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                environment.setdefault(key.strip(), value.strip())
    if len(environment.get("APP_ACCESS_TOKEN", "")) < 32:
        sys.exit("Run python scripts/init_local.py or configure APP_ACCESS_TOKEN (32+ characters).")
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

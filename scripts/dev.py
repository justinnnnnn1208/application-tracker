"""Run the local app or isolated public model/source diagnostics."""
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
    mode.add_argument("--check-model", action="store_true", help="Public model check: one response per case, stop at the first failed check; no app startup")
    mode.add_argument("--check-model-full", action="store_true", help="Full public model diagnostic run, including validation retries and later cases after failure")
    mode.add_argument('--check-discovery', choices=('greenhouse', 'lever', 'ashby', 'smartrecruiters', 'reed'), help='Read public source without importing or starting tracker services')
    parser.add_argument("--case", help="With a model check, diagnose just this reviewed case; other cases remain NOT TESTED")
    parser.add_argument('--explain-failure', action='store_true', help='With a selected public model case, print/save its rejected entry for inspection')
    for name in ('board', 'employer', 'region', 'query'):
        parser.add_argument('--' + name, help='Public discovery check source setting')
    args = parser.parse_args()
    if args.case is not None and not (args.check_model or args.check_model_full):
        parser.error('--case requires --check-model or --check-model-full')
    if args.explain_failure and (not args.case or not (args.check_model or args.check_model_full)):
        parser.error('--explain-failure requires a model check and --case')
    if not args.check_discovery and any(getattr(args, name) is not None for name in ('board', 'employer', 'region', 'query')):
        parser.error('Source settings require --check-discovery')
    os.umask(0o077)
    environment = os.environ.copy()
    environment.setdefault("NEXT_TELEMETRY_DISABLED", "1")
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                environment.setdefault(key.strip(), value.strip())
    if args.check_model or args.check_model_full or args.check_discovery:
        interpreter = ROOT / "apps/api/.venv/bin/python"
        if not interpreter.is_file():
            print("Install API dependencies first: run uv sync --frozen from apps/api, then return to the project root.")
            return 2
        kind = 'discovery' if args.check_discovery else 'requirements'
        report = ROOT / ".local" / f"{kind}-check-{uuid4().hex}.json"
        # Diagnostics exclude tracker/OAuth/database settings and inherited Python paths.
        # Only a selected Reed check receives its required provider read key.
        public_environment = {"PATH": environment.get("PATH", os.defpath), "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1"}
        if args.check_discovery:
            keys = ['URL_FETCH_ALLOWED_HOSTS', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
                    'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy', 'SSL_CERT_FILE', 'SSL_CERT_DIR']
            if args.check_discovery == 'reed':
                keys.append('REED_API_KEY')
            command = [str(interpreter), '-m', 'app.services.discovery_check', '--provider', args.check_discovery, '--output', str(report)]
            for name in ('board', 'employer', 'region', 'query'):
                if getattr(args, name) is not None:
                    command += ['--' + name, getattr(args, name)]
        else:
            keys = ['LLM_PROVIDER', 'LLM_MODEL', 'LLM_BASE_URL']
            command = [str(interpreter), "-m", "app.services.requirements_eval",
                       "--manifest", str(ROOT / "fixtures/eval/manifest-nov20.json"),
                       "--review", str(ROOT / "fixtures/eval/requirements-review.json"),
                       "--output", str(report)] + (["--fail-fast", "--single-attempt"] if args.check_model else []) + (["--case", args.case] if args.case is not None else [])
            if args.explain_failure:
                command.append('--explain-failure')
        public_environment.update({key: environment[key] for key in keys if key in environment})
        try:
            result = subprocess.run(command, cwd=ROOT / "apps/api", env=public_environment)
        except KeyboardInterrupt:
            print('Public check cancelled; no tracker services or migrations were started.')
            if report.is_file():
                print(f"Public {'source' if args.check_discovery else 'model'}-check report: {report.relative_to(ROOT)}")
            return 130
        if report.is_file():
            print(f"Public {'source' if args.check_discovery else 'model'}-check report: {report.relative_to(ROOT)}", flush=True)
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

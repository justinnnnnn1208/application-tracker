"""Create a local-only token without displaying it or replacing existing settings."""
import os
import base64
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.umask(0o077)
(root / "storage").mkdir(exist_ok=True, mode=0o700)
(root / ".local").mkdir(exist_ok=True, mode=0o700)
try:
    with (root / ".env").open("x") as file:
        file.write(f"APP_ACCESS_TOKEN={secrets.token_urlsafe(48)}\n")
    print("Created private .env with a generated access token; its value was not printed.")
except FileExistsError:
    print("Existing .env preserved.")

existing = (root / ".env").read_text()
if not any(line.startswith("OAUTH_ENCRYPTION_KEY=") for line in existing.splitlines()):
    with (root / ".env").open("a") as file:
        file.write(("" if existing.endswith("\n") else "\n") + "OAUTH_ENCRYPTION_KEY=" + base64.urlsafe_b64encode(secrets.token_bytes(32)).decode() + "\n")
    print("Added a private local OAuth encryption key; existing settings were preserved.")

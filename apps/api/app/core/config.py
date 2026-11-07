import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Settings:
    database_url: str
    access_token: str
    storage_dir: Path = ROOT / "storage"

    @classmethod
    def from_env(cls):
        token = os.environ.get("APP_ACCESS_TOKEN", "")
        if len(token) < 32:
            raise RuntimeError("APP_ACCESS_TOKEN must contain at least 32 characters")
        storage = Path(os.environ.get("STORAGE_DIR", ROOT / "storage"))
        storage.mkdir(parents=True, exist_ok=True, mode=0o700)
        return cls(os.environ.get("DATABASE_URL", f"sqlite:///{storage / 'tracker.db'}"), token, storage)

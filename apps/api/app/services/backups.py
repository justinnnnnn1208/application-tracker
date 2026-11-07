"""Private ZIP backups with checksums and restoration into a new directory only."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from uuid import uuid4
import zipfile

from sqlalchemy.engine import make_url
from app.services.errors import NeedsInput


def restore(archive: Path, destination: Path):
    if destination.exists():
        raise ValueError("Restore destination must not exist")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".restore-") as staging:
        staging = Path(staging)
        with zipfile.ZipFile(archive) as file:
            members = file.infolist()
            if sum(item.file_size for item in members) > 2_000_000_000:
                raise ValueError("Backup is too large")
            for item in members:
                path = Path(item.filename)
                if path.is_absolute() or ".." in path.parts or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Unsafe archive member")
            manifest = json.loads(file.read("manifest.json"))
            if set(file.namelist()) != set(manifest["files"]) | {"manifest.json"}:
                raise ValueError("Unexpected archive members")
            for name, expected in manifest["files"].items():
                data = file.read(name)
                if hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError("Backup checksum mismatch")
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with target.open("xb") as output:
                    output.write(data)
                target.chmod(0o600)
        with sqlite3.connect(staging / "database.sqlite3") as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Database integrity check failed")
        staging.rename(destination)


def backup(settings, destination: Path):
    os.umask(0o077)
    storage = settings.storage_dir.resolve()
    destination = destination.expanduser().resolve()
    if destination == storage or destination.is_relative_to(storage):
        raise NeedsInput("Choose a backup folder outside the storage folder.")
    url = make_url(settings.database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise NeedsInput("The local backup command currently supports file-based SQLite databases.")
    database = Path(url.database).resolve()
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = datetime.now(timezone.utc).strftime("tracker-%Y%m%dT%H%M%SZ-") + uuid4().hex[:8] + ".zip"
    archive = destination / name
    with tempfile.TemporaryDirectory(prefix="tracker-backup-") as directory:
        snapshot = Path(directory) / "database.sqlite3"
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as source, sqlite3.connect(snapshot) as target:
            source.backup(target)
        files = {"database.sqlite3": snapshot}
        for path in storage.rglob("*"):
            if path.is_symlink():
                raise NeedsInput("Storage contains a symlink. Review it before backing up.")
            if path.is_file() and path.resolve() not in {database, Path(str(database) + "-wal"), Path(str(database) + "-shm")} and not path.name.startswith(".worker"):
                files["storage/" + str(path.relative_to(storage))] = path
        hashes = {}
        partial = archive.with_suffix(".partial")
        try:
            with zipfile.ZipFile(partial, "x", compression=zipfile.ZIP_DEFLATED) as file:
                for member, source in files.items():
                    data = source.read_bytes()
                    hashes[member] = hashlib.sha256(data).hexdigest()
                    file.writestr(member, data)
                file.writestr("manifest.json", json.dumps({"version": 1, "files": hashes}))
            # Every backup is restored and checked before it is presented as successful.
            restored = Path(directory) / "verified-restore"
            restore(partial, restored)
            partial.replace(archive)
            archive.chmod(0o600)
        finally:
            partial.unlink(missing_ok=True)
    return {"archive": str(archive), "restore_verified": True, "files": len(hashes)}

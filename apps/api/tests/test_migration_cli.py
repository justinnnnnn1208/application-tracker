import fcntl
import os
from pathlib import Path
import sqlite3

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import Settings
from app.services.backups import restore
from app.services.errors import NeedsInput
from app.services.migration_cli import migrate, require_current_schema


def test_helper_backs_up_and_restore_verifies_legacy_database_before_upgrade(tmp_path, monkeypatch):
    database = tmp_path / 'custom' / 'owner.db'
    database.parent.mkdir()
    url = f'sqlite:///{database}'
    monkeypatch.setenv('DATABASE_URL', url)
    command.upgrade(Config('alembic.ini'), '5103adc629a6')
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO profile (id, display_name, email, target_locations, graduation_year) VALUES (1, 'Fixture owner', '', 'Leeds', 2027)")
    storage = tmp_path / 'storage'
    storage.mkdir()
    (storage / 'fixture.txt').write_bytes(b'private-fixture-bytes')
    destination = tmp_path / 'backups'
    from app.db.session import make_engine
    engine = make_engine(url)
    with pytest.raises(RuntimeError, match='--migrate'):
        require_current_schema(engine)
    engine.dispose()
    original_upgrade = command.upgrade
    def verified_first(*args, **kwargs):
        assert list(destination.glob('*.zip'))
        return original_upgrade(*args, **kwargs)
    monkeypatch.setattr(command, 'upgrade', verified_first)
    # Explicit settings must win over a different inherited DB location.
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///unused.db')
    settings = Settings(url, 'fixture-only-long-token-' * 3, storage)
    result = migrate(settings, destination)
    assert result['restore_verified'] is True
    assert os.environ['DATABASE_URL'] == 'sqlite:///unused.db'
    restored = tmp_path / 'restored'
    restore(Path(result['archive']), restored)
    with sqlite3.connect(restored / 'database.sqlite3') as db:
        assert db.execute('SELECT display_name FROM profile').fetchone()[0] == 'Fixture owner'
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '5103adc629a6'
    assert (restored / 'storage' / 'fixture.txt').read_bytes() == b'private-fixture-bytes'
    with sqlite3.connect(database) as db:
        from alembic.script import ScriptDirectory
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == ScriptDirectory.from_config(Config('alembic.ini')).get_current_head()


def test_helper_refuses_running_worker_and_does_not_attempt_upgrade(tmp_path, monkeypatch):
    storage = tmp_path / 'storage'
    storage.mkdir()
    monkeypatch.setattr(command, 'upgrade', lambda *_: pytest.fail('Must not migrate a running worker database'))
    with (storage / '.worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(NeedsInput, match='Stop the local app'):
            migrate(Settings(f'sqlite:///{tmp_path}/db.sqlite3', 'fixture-only-token-' * 3, storage), tmp_path / 'backups')


@pytest.mark.parametrize('url', ['sqlite:///file:legacy.db?uri=true', 'sqlite:///:memory:'])
def test_helper_rejects_unbacked_uri_and_memory_databases(tmp_path, url):
    with pytest.raises(NeedsInput, match='file-based SQLite'):
        migrate(Settings(url, 'fixture-only-token-' * 3, tmp_path / 'storage'), tmp_path / 'backups')

"""Back up and restore-verify existing SQLite data before applying local migrations."""
import fcntl
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from app.db.session import make_engine
from sqlalchemy.engine import make_url

from app.core.config import ROOT, Settings
from app.services.backups import backup
from app.services.errors import NeedsInput


def configuration():
    config = Config(str(ROOT / 'apps/api/alembic.ini'))
    config.set_main_option('script_location', str(ROOT / 'apps/api/app/db/migrations'))
    return config


def require_current_schema(engine):
    expected = ScriptDirectory.from_config(configuration()).get_current_head()
    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    if current != expected:
        raise RuntimeError('Database update required. Stop the app and run python3 scripts/dev.py --migrate from the project root.')


def migrate(settings, destination):
    url = make_url(settings.database_url)
    if url.get_backend_name() != 'sqlite' or not url.database or url.database == ':memory:' or url.database.startswith('file:') or 'uri' in url.query:
        raise NeedsInput('This migration helper supports local file-based SQLite only.')
    settings.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (settings.storage_dir / '.worker.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise NeedsInput('Stop the local app with Control+C before applying migrations.') from None
        saved = backup(settings, destination) if Path(url.database).is_file() else None
        previous = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = settings.database_url
        try:
            command.upgrade(configuration(), 'head')
        finally:
            if previous is None:
                os.environ.pop('DATABASE_URL', None)
            else:
                os.environ['DATABASE_URL'] = previous
    return saved


def main():
    os.umask(0o077)
    try:
        migrate(Settings.from_env(), ROOT / '.local/migration-backups')
    except NeedsInput as error:
        print(str(error))
        return 1
    except Exception:
        print('Migration failed; the app was not started. Preserve the original data and any verified backup in .local/migration-backups before reviewing the error.')
        return 1
    print('Local migrations applied. Any existing database/storage backup was restored and verified first.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

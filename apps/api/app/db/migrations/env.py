import os
from alembic import context
from app.core.config import ROOT
from app.db.models import Base
from app.db.session import make_engine

url = os.environ.get("DATABASE_URL", f"sqlite:///{ROOT / 'storage' / 'tracker.db'}")
if url.startswith("sqlite"):
    (ROOT / "storage").mkdir(parents=True, exist_ok=True, mode=0o700)

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()

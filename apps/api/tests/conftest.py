import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

# Test-only token. Never used by the development instance.
TOKEN = "test-only-access-token-00000000000000000000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    app = create_app(Settings(url, TOKEN, tmp_path / "storage"))
    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {TOKEN}"
        yield test_client

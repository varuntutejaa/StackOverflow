from __future__ import annotations

import os
import tempfile

import pytest

os.environ.setdefault("KAUSHAI_ENV", "test")
_tmp_db = os.path.join(tempfile.gettempdir(), "kaushai_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-prod"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed as seed_module  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_module.run(fresh=False)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


def _login(client, email, password):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def admin_token(client):
    return _login(client, "admin@kaushai.gov.in", "KaushAI@2026")


@pytest.fixture()
def officer_token(client):
    return _login(client, "officer@kaushai.gov.in", "Officer@2026")


@pytest.fixture()
def auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

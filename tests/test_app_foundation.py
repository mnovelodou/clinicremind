"""Tests for the F1 application skeleton (app-foundation capability).

The factory/config tests are pure unit tests (no database). The health-check
tests exercise the app↔database path for real, so they are integration tests
(``@pytest.mark.integration``) and run against Postgres; they skip when no
database is reachable.
"""

from __future__ import annotations

import pytest

from app import create_app
from app.config import ConfigError


# --- Unit: factory and config plumbing (no database) -----------------------


def test_create_app_builds_with_override(app):
    """The factory returns a configured app honouring config_override."""
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    assert app.config["SECRET_KEY"]


def test_create_app_requires_database_url(monkeypatch):
    """Missing DATABASE_URL fails fast rather than booting broken."""
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "x")
    with pytest.raises(ConfigError):
        create_app()


# --- Integration: real app↔database round trip (Postgres) ------------------


@pytest.mark.integration
def test_health_ok(pg_client):
    """Health endpoint returns 200 when the database is reachable."""
    resp = pg_client.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


@pytest.mark.integration
def test_index_is_health(pg_client):
    """Root route also serves the health check."""
    assert pg_client.get("/").status_code == 200

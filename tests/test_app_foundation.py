"""Tests for the F1 application skeleton (app-foundation capability)."""

from __future__ import annotations

import pytest

from app import create_app
from app.config import ConfigError


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


def test_health_ok(client):
    """Health endpoint returns 200 when the database is reachable."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_index_is_health(client):
    """Root route also serves the health check."""
    assert client.get("/").status_code == 200

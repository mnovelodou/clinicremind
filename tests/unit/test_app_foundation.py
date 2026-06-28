"""Unit tests for the app factory and config (app-foundation capability).

Pure unit tests: no database connection of any kind. ``db.init_app`` is mocked
so the factory is exercised without binding a real engine (SQLite or otherwise);
the config-failure path raises before any database is touched.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app import create_app
from app.config import ConfigError


def test_create_app_builds_with_override():
    """The factory returns a configured app honouring config_override.

    ``db.init_app`` is patched out so no engine is created — this asserts the
    factory/config plumbing only, with zero database involvement.
    """
    with patch("app.extensions.db.init_app") as mock_init:
        app = create_app(
            config_override={"SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://fake/db"}
        )
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "postgresql+psycopg://fake/db"
    assert app.config["SECRET_KEY"]
    mock_init.assert_called_once_with(app)


def test_create_app_requires_database_url(monkeypatch):
    """Missing DATABASE_URL fails fast rather than booting broken."""
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "x")
    with pytest.raises(ConfigError):
        create_app()

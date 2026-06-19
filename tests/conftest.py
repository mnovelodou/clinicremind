"""Pytest fixtures for the app skeleton."""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """A Flask app bound to an in-memory SQLite database for fast tests.

    Overriding the database URI proves the factory honours config_override; the
    health check's ``SELECT 1`` is dialect-agnostic, so SQLite is sufficient for
    skeleton-level tests.
    """
    app = create_app(config_override={"SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()

"""Shared pytest fixtures.

Two flavours of test live in this suite:

* **Unit** tests use the ``app``/``client`` fixtures below, backed by an
  in-memory SQLite database — fast, no external services.
* **Integration** tests (marked ``@pytest.mark.integration``) use the
  ``pg_engine``/``db_session`` fixtures, backed by a real Postgres, because they
  assert database-level guarantees (native enums, partial indexes, foreign
  keys) that SQLite does not honour. Start one with ``docker compose up -d db``.
  These tests skip cleanly when no Postgres is reachable.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
import app.models  # noqa: F401  (register tables on db.metadata)

# Dedicated test database (see docker-compose.yml). Kept separate from the
# development DATABASE_URL so a test run never wipes development data.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://clinicremind:clinicremind@localhost:5432/clinicremind_test",
)


# --- Unit-test fixtures (SQLite) -------------------------------------------


@pytest.fixture
def app():
    """A Flask app bound to an in-memory SQLite database for fast tests."""
    app = create_app(config_override={"SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


# --- Integration-test fixtures (Postgres) ----------------------------------


@pytest.fixture(scope="session")
def pg_engine():
    """A Postgres engine with the full schema; skips if unreachable.

    The schema is built directly from ``db.metadata`` (independent of migration
    state) and dropped at the end of the session.
    """
    if not TEST_DATABASE_URL.startswith("postgresql"):
        pytest.skip("integration tests require Postgres")
    engine = create_engine(TEST_DATABASE_URL)
    try:
        engine.connect().close()
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Postgres not reachable: {exc}")
    db.metadata.drop_all(engine)
    db.metadata.create_all(engine)
    yield engine
    db.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(pg_engine):
    """A transactional session rolled back after each test for isolation."""
    conn = pg_engine.connect()
    txn = conn.begin()
    session = Session(bind=conn)
    try:
        yield session
    finally:
        session.close()
        # A failed flush may have already rolled the transaction back.
        if txn.is_active:
            txn.rollback()
        conn.close()

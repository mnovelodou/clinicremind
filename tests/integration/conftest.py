"""Fixtures for integration tests — backed by a real Postgres.

Integration tests assert behaviour that only a real database provides (native
enums, partial indexes, foreign keys, a live ``SELECT``), so SQLite or a mock
would prove nothing. Start a database with ``docker compose up -d db``; these
tests skip cleanly when none is reachable.
"""

from __future__ import annotations

import os
import pathlib

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

_HERE = pathlib.Path(__file__).parent

from app import create_app
from app.extensions import db
import app.models  # noqa: F401  (register tables on db.metadata)

# Dedicated test database (see docker-compose.yml). Kept separate from the
# development DATABASE_URL so a test run never wipes development data.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://clinicremind:clinicremind@localhost:5432/clinicremind_test",
)

def pytest_collection_modifyitems(items):
    """Mark tests under tests/integration/ as integration.

    A subdirectory conftest's hook still receives every collected item, so we
    filter to those whose file lives under this directory.
    """
    for item in items:
        if _HERE in pathlib.Path(str(item.fspath)).parents:
            item.add_marker(pytest.mark.integration)


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
    # The trigram GIN index on patients.name needs this extension (the migration
    # installs it too; create_all does not run that step).
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
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


@pytest.fixture
def pg_app(pg_engine):
    """A Flask app bound to the real Postgres test database.

    Use for tests that exercise the app↔database path for real (e.g. the health
    check's ``SELECT 1``). Depends on ``pg_engine`` so it inherits the
    skip-if-unreachable behaviour.
    """
    app = create_app(config_override={"SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URL})
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def pg_client(pg_app):
    return pg_app.test_client()


@pytest.fixture
def make_clinic(pg_app):
    """Factory that creates clinics on the app session and cleans up only its own.

    Teardown deletes exactly the clinics this factory created (and their
    patients) by id — never a blanket ``DELETE`` — so tests stay independent of
    each other within the session-scoped schema.
    """
    from app.extensions import db
    from app.models import Clinic, Patient

    created_ids: list[int] = []

    def _make(name: str = "Test Clinic", default_country: str = "MX") -> Clinic:
        clinic = Clinic(
            name=name, timezone="America/Mexico_City", default_country=default_country
        )
        db.session.add(clinic)
        db.session.commit()
        created_ids.append(clinic.id)
        return clinic

    yield _make

    if created_ids:
        db.session.query(Patient).filter(
            Patient.clinic_id.in_(created_ids)
        ).delete(synchronize_session=False)
        db.session.query(Clinic).filter(
            Clinic.id.in_(created_ids)
        ).delete(synchronize_session=False)
        db.session.commit()

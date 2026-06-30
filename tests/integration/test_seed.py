"""Tests for the seed command (seed-data capability).

The dataset is written against a real Postgres (native enums, the partial unique
grant index, foreign keys), so these use the shared ``db_session`` fixture and
skip when no database is reachable. The production guard is a pure function and
is tested directly. Run a database with ``docker compose up -d db``.
"""

from __future__ import annotations

import pytest

from app.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    ClinicDoctor,
    ClinicMember,
    Doctor,
    DoctorReceptionistGrant,
    Patient,
    User,
)
from app.seed import DEV_PASSWORD, USERS, is_production, seed_database
from app.security import verify_password

# Tables touched by the seed, used for row-count comparisons.
_SEEDED_MODELS = [
    Clinic,
    User,
    ClinicMember,
    Doctor,
    ClinicDoctor,
    Patient,
    DoctorReceptionistGrant,
    Appointment,
]


def _counts(session) -> dict[str, int]:
    return {m.__tablename__: session.query(m).count() for m in _SEEDED_MODELS}


# --- 4.1 fresh seed --------------------------------------------------------


def test_seed_creates_expected_rows(db_session):
    seed_database(db_session)

    assert db_session.query(Clinic).count() == 1
    assert db_session.query(User).count() == len(USERS)
    assert db_session.query(Doctor).count() >= 3
    assert db_session.query(Patient).count() >= 15
    assert db_session.query(Appointment).count() >= 30


def test_seed_has_linked_and_unlinked_doctors(db_session):
    seed_database(db_session)
    doctors = db_session.query(Doctor).all()
    assert any(d.user_id is not None for d in doctors)
    assert any(d.user_id is None for d in doctors)


def test_seed_covers_every_appointment_status(db_session):
    seed_database(db_session)
    present = {a.status for a in db_session.query(Appointment).all()}
    assert present == set(AppointmentStatus)


def test_seed_appointments_span_past_today_future(db_session):
    from app.seed import _today_utc

    seed_database(db_session)
    today = _today_utc()
    starts = [a.start_at for a in db_session.query(Appointment).all()]
    assert any(s < today for s in starts)  # past
    assert any(today <= s < today.replace(hour=23) for s in starts)  # today
    assert any(s >= today.replace(hour=23) for s in starts)  # future days


def test_seed_creates_active_grant(db_session):
    seed_database(db_session)
    grants = db_session.query(DoctorReceptionistGrant).all()
    assert len(grants) >= 1
    assert any(g.revoked_at is None for g in grants)


def test_seed_passwords_are_hashed_not_plaintext(db_session):
    seed_database(db_session)
    for user in db_session.query(User).all():
        assert user.password_hash != DEV_PASSWORD
        assert verify_password(DEV_PASSWORD, user.password_hash)


def test_seed_patients_have_two_part_phone(db_session):
    seed_database(db_session)
    for patient in db_session.query(Patient).all():
        assert patient.country_code and patient.country_code.isdigit()
        assert patient.phone_national and patient.phone_national.isdigit()
        assert patient.phone_e164 == f"+{patient.country_code}{patient.phone_national}"


# --- 4.2 idempotency -------------------------------------------------------


def test_seed_is_idempotent(db_session):
    seed_database(db_session)
    db_session.flush()
    after_first = _counts(db_session)

    second = seed_database(db_session)
    db_session.flush()
    after_second = _counts(db_session)

    assert after_second == after_first
    assert sum(second.values()) == 0  # second run created nothing


# --- 4.3 production guard ---------------------------------------------------


@pytest.mark.parametrize("value", ["production", "Production", "  PRODUCTION  "])
def test_guard_blocks_production(monkeypatch, value):
    monkeypatch.setenv("APP_ENV", value)
    assert is_production() is True


@pytest.mark.parametrize("value", ["development", "test", "staging", ""])
def test_guard_allows_non_production(monkeypatch, value):
    monkeypatch.setenv("APP_ENV", value)
    assert is_production() is False


def test_guard_falls_back_to_flask_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    assert is_production() is True


def test_guard_allows_when_unset(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    assert is_production() is False


def test_seed_command_aborts_in_production(monkeypatch, pg_app):
    """The CLI command exits non-zero and writes nothing in production."""
    monkeypatch.setenv("APP_ENV", "production")
    runner = pg_app.test_cli_runner()
    result = runner.invoke(args=["seed"])
    assert result.exit_code == 1
    assert "Refusing to seed" in result.output

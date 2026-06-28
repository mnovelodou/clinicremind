"""Schema-invariant tests for the D1 data model (data-model capability).

These assert DB-level guarantees — native enum validation, unique email, the
no-duplicate-active-grant partial index, and foreign-key enforcement — so they
require Postgres (SQLite does not honour native enums or partial indexes). They
use the shared ``db_session`` fixture (see conftest) and skip when no database
is reachable. Run a database with ``docker compose up -d db``.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.models import (
    Clinic,
    ClinicDoctor,
    ClinicMember,
    Doctor,
    DoctorReceptionistGrant,
    MemberRole,
    Patient,
    User,
)

# Every test in this module needs a real Postgres.
pytestmark = pytest.mark.integration


def _clinic(session) -> Clinic:
    c = Clinic(name="Test Clinic", timezone="America/Mexico_City", default_country="MX")
    session.add(c)
    session.flush()
    return c


def test_unique_email(db_session):
    db_session.add(User(email="a@x.com", password_hash="h", name="A"))
    db_session.flush()
    db_session.add(User(email="a@x.com", password_hash="h", name="B"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_invalid_role_rejected(db_session):
    clinic = _clinic(db_session)
    user = User(email="r@x.com", password_hash="h", name="R")
    db_session.add(user)
    db_session.flush()
    # Bypass the Python enum to exercise the DB-level enum constraint.
    with pytest.raises(DBAPIError):
        db_session.execute(
            text(
                "INSERT INTO clinic_members (clinic_id, user_id, role) "
                "VALUES (:c, :u, 'super_admin')"
            ),
            {"c": clinic.id, "u": user.id},
        )


def test_invalid_appointment_status_rejected(db_session):
    clinic = _clinic(db_session)
    doctor = Doctor(name="Dr")
    patient = Patient(clinic_id=clinic.id, name="Pat")
    db_session.add_all([doctor, patient])
    db_session.flush()
    with pytest.raises(DBAPIError):
        db_session.execute(
            text(
                "INSERT INTO appointments "
                "(clinic_id, patient_id, doctor_id, start_at, end_at, status) "
                "VALUES (:c, :p, :d, now(), now(), 'bogus')"
            ),
            {"c": clinic.id, "p": patient.id, "d": doctor.id},
        )


def test_appointment_status_defaults_to_pending(db_session):
    clinic = _clinic(db_session)
    doctor = Doctor(name="Dr")
    patient = Patient(clinic_id=clinic.id, name="Pat")
    db_session.add_all([doctor, patient])
    db_session.flush()
    # Insert without a status, then read it back: the DB default is 'pending'.
    db_session.execute(
        text(
            "INSERT INTO appointments "
            "(clinic_id, patient_id, doctor_id, start_at, end_at) "
            "VALUES (:c, :p, :d, now(), now())"
        ),
        {"c": clinic.id, "p": patient.id, "d": doctor.id},
    )
    status = db_session.execute(text("SELECT status FROM appointments")).scalar_one()
    assert status == "pending"


def test_fk_enforced(db_session):
    # Membership referencing a non-existent clinic/user must be rejected.
    with pytest.raises(IntegrityError):
        db_session.add(
            ClinicMember(clinic_id=999999, user_id=999999, role=MemberRole.admin)
        )
        db_session.flush()


def test_no_duplicate_active_grant(db_session):
    clinic = _clinic(db_session)
    doctor = Doctor(name="Dr")
    recept = User(email="rec@x.com", password_hash="h", name="Rec")
    db_session.add_all([doctor, recept])
    db_session.flush()
    db_session.add(
        DoctorReceptionistGrant(
            clinic_id=clinic.id, doctor_id=doctor.id, receptionist_user_id=recept.id
        )
    )
    db_session.flush()
    # Second active grant for the same pair violates the partial unique index.
    db_session.add(
        DoctorReceptionistGrant(
            clinic_id=clinic.id, doctor_id=doctor.id, receptionist_user_id=recept.id
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_revoked_grant_allows_new_active_grant(db_session):
    clinic = _clinic(db_session)
    doctor = Doctor(name="Dr")
    recept = User(email="rec2@x.com", password_hash="h", name="Rec")
    db_session.add_all([doctor, recept])
    db_session.flush()
    g1 = DoctorReceptionistGrant(
        clinic_id=clinic.id, doctor_id=doctor.id, receptionist_user_id=recept.id
    )
    db_session.add(g1)
    db_session.flush()
    # Revoke, then a new active grant for the same pair is allowed.
    db_session.execute(
        text("UPDATE doctor_receptionist_grants SET revoked_at = now() WHERE id = :i"),
        {"i": g1.id},
    )
    db_session.add(
        DoctorReceptionistGrant(
            clinic_id=clinic.id, doctor_id=doctor.id, receptionist_user_id=recept.id
        )
    )
    db_session.flush()  # must not raise


def test_patient_has_no_clinical_columns(db_session):
    cols = set(Patient.__table__.columns.keys())
    assert cols == {
        "id",
        "clinic_id",
        "name",
        "country_code",
        "phone_national",
        "email",
        "notes",
        "created_at",
        "updated_at",
    }


def test_phone_e164_reconstructed_from_parts(db_session):
    clinic = _clinic(db_session)
    p = Patient(
        clinic_id=clinic.id, name="Pat", country_code="52", phone_national="5512345678"
    )
    db_session.add(p)
    db_session.flush()
    assert p.phone_e164 == "+525512345678"
    # No phone stored → no reconstruction.
    p2 = Patient(clinic_id=clinic.id, name="NoPhone")
    db_session.add(p2)
    db_session.flush()
    assert p2.phone_e164 is None


def test_partial_name_search(db_session):
    clinic = _clinic(db_session)
    db_session.add(Patient(clinic_id=clinic.id, name="Jose Miguel Novelo Vargas"))
    db_session.flush()
    # A middle-of-string fragment must match (trigram GIN index backs this).
    found = (
        db_session.query(Patient)
        .filter(Patient.clinic_id == clinic.id, Patient.name.ilike("%novelo%"))
        .all()
    )
    assert len(found) == 1
    assert found[0].name == "Jose Miguel Novelo Vargas"


def test_doctor_works_at_multiple_clinics(db_session):
    a = Clinic(name="Clinic A", timezone="America/Mexico_City", default_country="MX")
    b = Clinic(name="Clinic B", timezone="America/Mexico_City", default_country="MX")
    doctor = Doctor(name="Dr Multi")
    db_session.add_all([a, b, doctor])
    db_session.flush()
    db_session.add_all(
        [
            ClinicDoctor(clinic_id=a.id, doctor_id=doctor.id),
            ClinicDoctor(clinic_id=b.id, doctor_id=doctor.id),
        ]
    )
    db_session.flush()  # same doctor in two clinics is allowed
    links = (
        db_session.query(ClinicDoctor)
        .filter(ClinicDoctor.doctor_id == doctor.id)
        .count()
    )
    assert links == 2


def test_no_duplicate_clinic_doctor(db_session):
    clinic = _clinic(db_session)
    doctor = Doctor(name="Dr")
    db_session.add_all([clinic, doctor])
    db_session.flush()
    db_session.add(ClinicDoctor(clinic_id=clinic.id, doctor_id=doctor.id))
    db_session.flush()
    # Same (clinic, doctor) twice violates the unique constraint.
    db_session.add(ClinicDoctor(clinic_id=clinic.id, doctor_id=doctor.id))
    with pytest.raises(IntegrityError):
        db_session.flush()

"""Integration tests for PatientRepository against a real Postgres.

Repository behaviour (clinic scoping, name ordering, the list safety cap) is
verified against the actual database rather than a mocked session — mocking
SQLAlchemy query chains tests the mock, not the query. Uses the ``make_clinic``
factory for isolated, self-cleaning data; skips when no database is reachable.
"""

from __future__ import annotations

from app.extensions import db
from app.models import Patient
from app.repositories.patient_repository import PatientRepository


def _repo() -> PatientRepository:
    return PatientRepository(db.session)


def test_create_then_get_for_clinic(make_clinic):
    clinic = make_clinic()
    created = _repo().create(
        Patient(clinic_id=clinic.id, name="Ana", country_code="52",
                phone_national="5512345678")
    )
    assert created.id is not None

    got = _repo().get_for_clinic(clinic.id, created.id)
    assert got is not None
    assert got.name == "Ana"


def test_get_for_clinic_is_scoped(make_clinic):
    clinic = make_clinic("A")
    other = make_clinic("B")
    stranger = _repo().create(Patient(clinic_id=other.id, name="Stranger"))

    # Not visible from a different clinic.
    assert _repo().get_for_clinic(clinic.id, stranger.id) is None


def test_list_is_ordered_by_name(make_clinic):
    clinic = make_clinic()
    for name in ["Carla", "Ana", "Bruno"]:
        _repo().create(Patient(clinic_id=clinic.id, name=name))

    names = [p.name for p in _repo().list_for_clinic(clinic.id)]
    assert names == ["Ana", "Bruno", "Carla"]


def test_list_respects_limit_and_offset(make_clinic):
    clinic = make_clinic()
    for i in range(5):
        _repo().create(Patient(clinic_id=clinic.id, name=f"P{i}"))

    first_two = _repo().list_for_clinic(clinic.id, limit=2)
    assert [p.name for p in first_two] == ["P0", "P1"]

    next_two = _repo().list_for_clinic(clinic.id, limit=2, offset=2)
    assert [p.name for p in next_two] == ["P2", "P3"]

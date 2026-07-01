"""Route tests for patient create/edit (patient-management capability).

These exercise the real request→database path, so they use the ``pg_app`` /
``pg_client`` fixtures and skip when no Postgres is reachable. Each test creates
its own clinic (and any second clinic it needs) and cleans up afterwards so the
session-scoped schema stays free of cross-test residue.
"""

from __future__ import annotations

import pytest

from app.extensions import db
from app.models import Clinic, Patient


def _make_clinic(name: str, default_country: str = "MX") -> Clinic:
    clinic = Clinic(
        name=name, timezone="America/Mexico_City", default_country=default_country
    )
    db.session.add(clinic)
    db.session.commit()
    return clinic


@pytest.fixture
def clinic(pg_app):
    """A committed clinic for the app's session; torn down after the test."""
    created = _make_clinic("P1 Test Clinic")
    yield created
    db.session.query(Patient).delete()
    db.session.query(Clinic).delete()
    db.session.commit()


def test_create_persists_normalized_phone(pg_client, clinic):
    resp = pg_client.post(
        "/patients/",
        data={"name": "Ana Gomez", "phone": "55 1234 5678", "email": "ana@example.com"},
    )
    # HTMX success: empty body + redirect header.
    assert resp.status_code == 200
    assert resp.headers.get("HX-Redirect") == "/patients/"

    patient = db.session.query(Patient).filter_by(name="Ana Gomez").one()
    assert patient.clinic_id == clinic.id
    assert patient.country_code == "52"
    assert patient.phone_national == "5512345678"
    assert patient.email == "ana@example.com"


def test_create_missing_name_rerenders_error(pg_client, clinic):
    resp = pg_client.post("/patients/", data={"name": "", "phone": "5512345678"})
    assert resp.status_code == 200
    assert "HX-Redirect" not in resp.headers
    body = resp.get_data(as_text=True)
    assert "Name is required." in body
    # Submitted phone is preserved in the re-rendered form.
    assert "5512345678" in body
    assert db.session.query(Patient).count() == 0


def test_edit_prefills_and_persists(pg_client, clinic):
    patient = Patient(
        clinic_id=clinic.id, name="Old Name", country_code="52",
        phone_national="5512345678",
    )
    db.session.add(patient)
    db.session.commit()
    original_updated_at = patient.updated_at

    # GET pre-fills current values.
    form = pg_client.get(f"/patients/{patient.id}/edit").get_data(as_text=True)
    assert "Old Name" in form
    assert "+525512345678" in form

    # POST persists the change and advances updated_at.
    resp = pg_client.post(
        f"/patients/{patient.id}",
        data={"name": "New Name", "phone": "+525512345678"},
    )
    assert resp.headers.get("HX-Redirect") == "/patients/"
    db.session.refresh(patient)
    assert patient.name == "New Name"
    assert patient.updated_at >= original_updated_at


def test_edit_patient_from_other_clinic_404s(pg_client, clinic):
    other = _make_clinic("Other Clinic")
    stranger = Patient(clinic_id=other.id, name="Not Mine")
    db.session.add(stranger)
    db.session.commit()

    # current_clinic() resolves to the lowest-id clinic (the `clinic` fixture),
    # so a patient in `other` is not visible.
    assert pg_client.get(f"/patients/{stranger.id}/edit").status_code == 404
    resp = pg_client.post(f"/patients/{stranger.id}", data={"name": "Hacked"})
    assert resp.status_code == 404
    db.session.refresh(stranger)
    assert stranger.name == "Not Mine"

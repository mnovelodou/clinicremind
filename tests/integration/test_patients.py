"""Route tests for patient create/edit (patient-management capability).

These exercise the real request→database path, so they use the ``pg_app`` /
``pg_client`` fixtures and skip when no Postgres is reachable. Clinics come from
the ``make_clinic`` factory (see conftest), which cleans up only the rows it
created.
"""

from __future__ import annotations

import time

from app.extensions import db
from app.models import Patient


def test_create_persists_normalized_phone(pg_client, make_clinic):
    clinic = make_clinic("P1 Test Clinic")
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


def test_create_missing_name_rerenders_error(pg_client, make_clinic):
    make_clinic("P1 Test Clinic")
    resp = pg_client.post("/patients/", data={"name": "", "phone": "5512345678"})
    assert resp.status_code == 200
    assert "HX-Redirect" not in resp.headers
    body = resp.get_data(as_text=True)
    assert "Name is required." in body
    # Submitted phone is preserved in the re-rendered form.
    assert "5512345678" in body
    assert db.session.query(Patient).count() == 0


def test_edit_prefills_and_persists(pg_client, make_clinic):
    clinic = make_clinic("P1 Test Clinic")
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

    # Ensure a distinguishable transaction timestamp for the update below.
    time.sleep(0.01)

    # POST persists the change and strictly advances updated_at.
    resp = pg_client.post(
        f"/patients/{patient.id}",
        data={"name": "New Name", "phone": "+525512345678"},
    )
    assert resp.headers.get("HX-Redirect") == "/patients/"
    db.session.refresh(patient)
    assert patient.name == "New Name"
    assert patient.updated_at > original_updated_at


def test_edit_patient_from_other_clinic_404s(pg_client, make_clinic):
    make_clinic("P1 Test Clinic")  # lowest id → the current clinic
    other = make_clinic("Other Clinic")
    stranger = Patient(clinic_id=other.id, name="Not Mine")
    db.session.add(stranger)
    db.session.commit()

    # current_clinic() resolves to the lowest-id clinic, so a patient in
    # `other` is not visible.
    assert pg_client.get(f"/patients/{stranger.id}/edit").status_code == 404
    resp = pg_client.post(f"/patients/{stranger.id}", data={"name": "Hacked"})
    assert resp.status_code == 404
    db.session.refresh(stranger)
    assert stranger.name == "Not Mine"

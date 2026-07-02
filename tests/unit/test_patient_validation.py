"""Unit tests for patient input validation (patient-management capability).

Pure function — no database, no request context. ``build_patient_fields`` takes
a ``PatientFormData`` and returns the normalized column values plus a
field→error map.
"""

from __future__ import annotations

from app.schemas.patient_dto import PatientFormData
from app.services.patient_service import build_patient_fields


def test_valid_input_normalizes_and_reports_no_errors():
    fields, errors = build_patient_fields(
        PatientFormData(
            name="Ana Gomez",
            phone="55 1234 5678",
            email="ana@example.com",
            notes="prefers mornings",
        ),
        "MX",
    )
    assert errors == {}
    assert fields["name"] == "Ana Gomez"
    assert fields["country_code"] == "52"
    assert fields["phone_national"] == "5512345678"
    assert fields["email"] == "ana@example.com"
    assert fields["notes"] == "prefers mornings"


def test_missing_name_is_an_error():
    _fields, errors = build_patient_fields(PatientFormData(name=""), "MX")
    assert "name" in errors


def test_blank_optional_fields_become_null():
    fields, errors = build_patient_fields(PatientFormData(name="Solo"), "MX")
    assert errors == {}
    assert fields["country_code"] is None
    assert fields["phone_national"] is None
    assert fields["email"] is None
    assert fields["notes"] is None


def test_malformed_email_is_an_error():
    _fields, errors = build_patient_fields(
        PatientFormData(name="Ana", email="not-an-email"), "MX"
    )
    assert "email" in errors


def test_phone_with_no_digits_is_an_error():
    _fields, errors = build_patient_fields(
        PatientFormData(name="Ana", phone="abc"), "MX"
    )
    assert "phone" in errors

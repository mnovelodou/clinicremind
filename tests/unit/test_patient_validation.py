"""Unit tests for patient form validation (patient-management capability).

Pure function — no database. ``validate_patient_form`` takes a plain mapping so
it can be exercised without a request context.
"""

from __future__ import annotations

from app.patients import validate_patient_form


def test_valid_input_normalizes_and_reports_no_errors():
    fields, values, errors = validate_patient_form(
        {"name": "Ana Gomez", "phone": "55 1234 5678", "email": "ana@example.com",
         "notes": "prefers mornings"},
        "MX",
    )
    assert errors == {}
    assert fields["name"] == "Ana Gomez"
    assert fields["country_code"] == "52"
    assert fields["phone_national"] == "5512345678"
    assert fields["email"] == "ana@example.com"
    assert fields["notes"] == "prefers mornings"
    # Raw input is echoed back for re-rendering.
    assert values["phone"] == "55 1234 5678"


def test_missing_name_is_an_error():
    fields, _values, errors = validate_patient_form({"name": "   "}, "MX")
    assert "name" in errors


def test_blank_optional_fields_become_null():
    fields, _values, errors = validate_patient_form({"name": "Solo"}, "MX")
    assert errors == {}
    assert fields["country_code"] is None
    assert fields["phone_national"] is None
    assert fields["email"] is None
    assert fields["notes"] is None


def test_malformed_email_is_an_error():
    _fields, _values, errors = validate_patient_form(
        {"name": "Ana", "email": "not-an-email"}, "MX"
    )
    assert "email" in errors


def test_phone_with_no_digits_is_an_error():
    _fields, _values, errors = validate_patient_form(
        {"name": "Ana", "phone": "abc"}, "MX"
    )
    assert "phone" in errors

"""Unit tests for the patient service (patient-management capability).

No database: the repository is a plain ``Mock`` (we assert the service's
orchestration and error translation, not SQLAlchemy). ``build_patient_fields`` is
a pure function tested directly. Repository behaviour against a real database is
covered by ``tests/integration/test_patient_repository.py``.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models import Patient
from app.schemas.patient_dto import CreatePatientDTO, UpdatePatientDTO
from app.services.exceptions import PatientNotFound, PersistenceError, ValidationError
from app.services.patient_service import PatientService, build_patient_fields


# --- build_patient_fields (pure validation/normalization) ------------------


def test_build_fields_valid_normalizes_and_reports_no_errors():
    fields, errors = build_patient_fields(
        CreatePatientDTO(
            name="Ana Gomez", phone="55 1234 5678", email="ana@example.com",
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


def test_build_fields_missing_name_is_an_error():
    _fields, errors = build_patient_fields(CreatePatientDTO(name=""), "MX")
    assert "name" in errors


def test_build_fields_blank_optionals_become_null():
    fields, errors = build_patient_fields(CreatePatientDTO(name="Solo"), "MX")
    assert errors == {}
    assert fields["country_code"] is None
    assert fields["phone_national"] is None
    assert fields["email"] is None
    assert fields["notes"] is None


def test_build_fields_malformed_email_is_an_error():
    _fields, errors = build_patient_fields(
        CreatePatientDTO(name="Ana", email="not-an-email"), "MX"
    )
    assert "email" in errors


def test_build_fields_phone_with_no_digits_is_an_error():
    _fields, errors = build_patient_fields(
        CreatePatientDTO(name="Ana", phone="abc"), "MX"
    )
    assert "phone" in errors


# --- PatientService.create -------------------------------------------------


def test_create_persists_a_patient_model_and_returns_dto():
    repo = Mock()
    repo.create.side_effect = lambda patient: patient  # echo the model back
    service = PatientService(repo)

    dto = service.create(1, CreatePatientDTO(name="Ana", phone="55 1234 5678"), "MX")

    assert dto.name == "Ana"
    assert dto.country_code == "52"
    assert dto.phone_national == "5512345678"
    # The repository is handed a Patient model (not loose kwargs).
    (passed,) = repo.create.call_args.args
    assert isinstance(passed, Patient)
    assert passed.clinic_id == 1


def test_create_invalid_input_raises_and_skips_persistence():
    repo = Mock()
    service = PatientService(repo)

    with pytest.raises(ValidationError) as exc:
        service.create(1, CreatePatientDTO(name=""), "MX")

    assert "name" in exc.value.errors
    repo.create.assert_not_called()


def test_create_wraps_db_error_as_persistence_error():
    repo = Mock()
    repo.create.side_effect = SQLAlchemyError("boom")
    service = PatientService(repo)

    with pytest.raises(PersistenceError):
        service.create(1, CreatePatientDTO(name="Ana"), "MX")


# --- PatientService.get_for_edit -------------------------------------------


def test_get_for_edit_missing_raises_not_found():
    repo = Mock()
    repo.get_for_clinic.return_value = None
    with pytest.raises(PatientNotFound):
        PatientService(repo).get_for_edit(1, 99)


def test_get_for_edit_returns_dto_with_display_phone():
    repo = Mock()
    repo.get_for_clinic.return_value = Patient(
        id=5, clinic_id=1, name="Ana", country_code="52", phone_national="5512345678"
    )
    dto = PatientService(repo).get_for_edit(1, 5)
    assert dto.id == 5
    assert dto.phone_display == "+525512345678"


# --- PatientService.update -------------------------------------------------


def test_update_missing_raises_not_found_before_validation():
    repo = Mock()
    repo.get_for_clinic.return_value = None
    with pytest.raises(PatientNotFound):
        PatientService(repo).update(1, 99, UpdatePatientDTO(name=""), "MX")
    repo.save.assert_not_called()


def test_update_invalid_input_raises_and_skips_save():
    repo = Mock()
    repo.get_for_clinic.return_value = Patient(id=5, clinic_id=1, name="Old")
    with pytest.raises(ValidationError):
        PatientService(repo).update(1, 5, UpdatePatientDTO(name=""), "MX")
    repo.save.assert_not_called()


def test_update_applies_fields_and_saves():
    repo = Mock()
    patient = Patient(id=5, clinic_id=1, name="Old")
    repo.get_for_clinic.return_value = patient
    repo.save.side_effect = lambda p: p

    dto = PatientService(repo).update(
        1, 5, UpdatePatientDTO(name="New", phone="55 1234 5678"), "MX"
    )

    assert patient.name == "New"
    assert patient.country_code == "52"
    assert patient.phone_national == "5512345678"
    assert dto.name == "New"
    repo.save.assert_called_once()

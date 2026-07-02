"""Patient use cases: list, load-for-edit, create, update.

Business rules (validation, phone normalization) live here, not in routes.
Input arrives as ``PatientFormData``; results leave as ``PatientDTO``. Failures
raise ``ValidationError`` / ``PatientNotFound`` — never HTTP.
"""

from __future__ import annotations

import re

from app.mappers import patient_mapper
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_dto import PatientDTO, PatientFormData
from app.services.exceptions import PatientNotFound, ValidationError
from app.utils.phone import normalize_phone

# Pragmatic email shape check — not full RFC validation, just enough to catch
# obvious typos. Stricter validation can come with a real verification flow.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def build_patient_fields(
    form: PatientFormData, default_country: str | None
) -> tuple[dict, dict]:
    """Validate + normalize input into persistence-ready fields.

    Pure function (no I/O): returns ``(fields, errors)`` where ``fields`` are the
    normalized column values and ``errors`` maps field → message. When ``errors``
    is non-empty the ``fields`` should not be persisted. Unit-testable without a
    database or request context.
    """
    errors: dict[str, str] = {}

    if not form.name:
        errors["name"] = "Name is required."

    country_code, phone_national = normalize_phone(form.phone, default_country)
    if form.phone and phone_national is None:
        errors["phone"] = "Enter a valid phone number."

    if form.email and not _EMAIL_RE.match(form.email):
        errors["email"] = "Enter a valid email address."

    fields = {
        "name": form.name,
        "country_code": country_code,
        "phone_national": phone_national,
        "email": form.email or None,
        "notes": form.notes or None,
    }
    return fields, errors


class PatientService:
    """Patient use cases, orchestrating the repository and mapper."""

    def __init__(self, repository: PatientRepository) -> None:
        self._repository = repository

    def list_for_clinic(self, clinic_id: int) -> list[PatientDTO]:
        """Every patient in the clinic, as DTOs."""
        patients = self._repository.list_for_clinic(clinic_id)
        return [patient_mapper.to_dto(p) for p in patients]

    def get_for_edit(self, clinic_id: int, patient_id: int) -> PatientDTO:
        """Load one patient for editing, or raise ``PatientNotFound``."""
        patient = self._repository.get_for_clinic(clinic_id, patient_id)
        if patient is None:
            raise PatientNotFound(patient_id)
        return patient_mapper.to_dto(patient)

    def create(
        self, clinic_id: int, form: PatientFormData, default_country: str | None
    ) -> PatientDTO:
        """Validate and create a patient. Raises ``ValidationError`` on bad input."""
        fields, errors = build_patient_fields(form, default_country)
        if errors:
            raise ValidationError(errors)
        patient = self._repository.create(clinic_id=clinic_id, **fields)
        return patient_mapper.to_dto(patient)

    def update(
        self,
        clinic_id: int,
        patient_id: int,
        form: PatientFormData,
        default_country: str | None,
    ) -> PatientDTO:
        """Validate and update an existing clinic patient.

        Raises ``PatientNotFound`` if the patient isn't in this clinic (checked
        first, so a stranger's id is never revealed as merely invalid), then
        ``ValidationError`` on bad input.
        """
        patient = self._repository.get_for_clinic(clinic_id, patient_id)
        if patient is None:
            raise PatientNotFound(patient_id)

        fields, errors = build_patient_fields(form, default_country)
        if errors:
            raise ValidationError(errors)

        patient.name = fields["name"]
        patient.country_code = fields["country_code"]
        patient.phone_national = fields["phone_national"]
        patient.email = fields["email"]
        patient.notes = fields["notes"]
        self._repository.save(patient)
        return patient_mapper.to_dto(patient)

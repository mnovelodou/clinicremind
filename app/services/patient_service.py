"""Patient use cases: list, load-for-edit, create, update.

Business rules (validation, phone normalization) live here, not in routes.
Input arrives as write DTOs (``CreatePatientDTO`` / ``UpdatePatientDTO``);
results leave as ``PatientDTO``. The service never sees framework input
(``request``/``FormData``), so a future REST endpoint can reuse it as-is.
Failures raise domain exceptions — never HTTP.
"""

from __future__ import annotations

import re

from sqlalchemy.exc import SQLAlchemyError

from app.mappers import patient_mapper
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_dto import CreatePatientDTO, PatientDTO, UpdatePatientDTO
from app.services.exceptions import PatientNotFound, PersistenceError, ValidationError
from app.utils.phone import normalize_phone

# Pragmatic email shape check — not full RFC validation, just enough to catch
# obvious typos. Stricter validation can come with a real verification flow.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def build_patient_fields(
    data: CreatePatientDTO | UpdatePatientDTO, default_country: str | None
) -> tuple[dict, dict]:
    """Validate + normalize a create/update input DTO into persistence-ready fields.

    Pure function (no I/O): returns ``(fields, errors)`` where ``fields`` are the
    normalized column values and ``errors`` maps field → message. When ``errors``
    is non-empty the ``fields`` should not be persisted. Unit-testable without a
    database or request context.
    """
    errors: dict[str, str] = {}

    if not data.name:
        errors["name"] = "Name is required."

    country_code, phone_national = normalize_phone(data.phone, default_country)
    if data.phone and phone_national is None:
        errors["phone"] = "Enter a valid phone number."

    if data.email and not _EMAIL_RE.match(data.email):
        errors["email"] = "Enter a valid email address."

    fields = {
        "name": data.name,
        "country_code": country_code,
        "phone_national": phone_national,
        "email": data.email or None,
        "notes": data.notes or None,
    }
    return fields, errors


class PatientService:
    """Patient use cases, orchestrating the repository and mapper."""

    def __init__(self, repository: PatientRepository) -> None:
        self._repository = repository

    def list_for_clinic(self, clinic_id: int) -> list[PatientDTO]:
        """Every patient in the clinic (bounded), as DTOs."""
        try:
            patients = self._repository.list_for_clinic(clinic_id)
        except SQLAlchemyError as exc:
            raise PersistenceError() from exc
        return [patient_mapper.to_patient_dto(p) for p in patients]

    def get_for_edit(self, clinic_id: int, patient_id: int) -> PatientDTO:
        """Load one patient for editing, or raise ``PatientNotFound``."""
        try:
            patient = self._repository.get_for_clinic(clinic_id, patient_id)
        except SQLAlchemyError as exc:
            raise PersistenceError() from exc
        if patient is None:
            raise PatientNotFound(patient_id)
        return patient_mapper.to_patient_dto(patient)

    def create(
        self, clinic_id: int, data: CreatePatientDTO, default_country: str | None
    ) -> PatientDTO:
        """Validate and create a patient. Raises ``ValidationError`` on bad input."""
        fields, errors = build_patient_fields(data, default_country)
        if errors:
            raise ValidationError(errors)
        patient = patient_mapper.to_model(clinic_id, fields)
        try:
            patient = self._repository.create(patient)
        except SQLAlchemyError as exc:
            raise PersistenceError() from exc
        return patient_mapper.to_patient_dto(patient)

    def update(
        self,
        clinic_id: int,
        patient_id: int,
        data: UpdatePatientDTO,
        default_country: str | None,
    ) -> PatientDTO:
        """Validate and update an existing clinic patient.

        Raises ``PatientNotFound`` if the patient isn't in this clinic (checked
        first, so a stranger's id is never revealed as merely invalid), then
        ``ValidationError`` on bad input.
        """
        try:
            patient = self._repository.get_for_clinic(clinic_id, patient_id)
        except SQLAlchemyError as exc:
            raise PersistenceError() from exc
        if patient is None:
            raise PatientNotFound(patient_id)

        fields, errors = build_patient_fields(data, default_country)
        if errors:
            raise ValidationError(errors)

        patient_mapper.apply_fields(patient, fields)
        try:
            patient = self._repository.save(patient)
        except SQLAlchemyError as exc:
            raise PersistenceError() from exc
        return patient_mapper.to_patient_dto(patient)

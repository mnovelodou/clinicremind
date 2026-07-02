"""Patient ORM ↔ DTO conversions."""

from __future__ import annotations

from app.models import Patient
from app.schemas.patient_dto import PatientDTO
from app.utils.phone import format_phone_input


def to_dto(patient: Patient) -> PatientDTO:
    """Convert a ``Patient`` model into a persistence-free ``PatientDTO``."""
    return PatientDTO(
        id=patient.id,
        clinic_id=patient.clinic_id,
        name=patient.name,
        country_code=patient.country_code,
        phone_national=patient.phone_national,
        phone_e164=patient.phone_e164,
        phone_display=format_phone_input(patient.country_code, patient.phone_national),
        email=patient.email,
        notes=patient.notes,
    )

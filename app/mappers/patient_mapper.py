"""Patient ORM ↔ DTO conversions.

Naming: ``to_<x>_dto`` builds a DTO from a model; ``to_model`` builds/updates a
model from validated data. This is the only place that knows both shapes.
"""

from __future__ import annotations

from app.models import Patient
from app.schemas.patient_dto import PatientDTO
from app.utils.phone import format_phone_input


def to_patient_dto(patient: Patient) -> PatientDTO:
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


def to_model(clinic_id: int, fields: dict) -> Patient:
    """Build a new ``Patient`` model from validated, normalized fields."""
    return Patient(clinic_id=clinic_id, **fields)


def apply_fields(patient: Patient, fields: dict) -> Patient:
    """Copy validated, normalized fields onto an existing ``Patient`` model."""
    for key, value in fields.items():
        setattr(patient, key, value)
    return patient

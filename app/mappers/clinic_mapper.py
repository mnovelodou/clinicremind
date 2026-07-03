"""Clinic ORM ↔ DTO conversions."""

from __future__ import annotations

from app.models import Clinic
from app.schemas.clinic_dto import ClinicDTO


def to_clinic_dto(clinic: Clinic) -> ClinicDTO:
    """Convert a ``Clinic`` model into a ``ClinicDTO``."""
    return ClinicDTO(
        id=clinic.id,
        name=clinic.name,
        timezone=clinic.timezone,
        default_country=clinic.default_country,
    )

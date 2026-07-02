"""Clinic ORM ↔ DTO conversions."""

from __future__ import annotations

from app.models import Clinic
from app.schemas.clinic_dto import ClinicContext


def to_context(clinic: Clinic) -> ClinicContext:
    """Convert a ``Clinic`` model into a ``ClinicContext`` DTO."""
    return ClinicContext(
        id=clinic.id,
        name=clinic.name,
        timezone=clinic.timezone,
        default_country=clinic.default_country,
    )

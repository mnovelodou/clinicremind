"""Patient DTOs — the patient shapes exposed across layer boundaries.

Naming: every DTO ends in ``DTO``. Write-side input DTOs are ``CreatePatientDTO``
/ ``UpdatePatientDTO`` (what a caller submits); ``PatientDTO`` is the read-side
shape returned to callers. Routes translate framework-specific input (an HTMX
form, later a JSON body) into these DTOs before calling a service — services
never see ``request``/``FormData``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PatientWriteDTO:
    """Base for patient write input — raw, unvalidated field values.

    Values are stripped of surrounding whitespace on construction. Concrete
    ``CreatePatientDTO`` / ``UpdatePatientDTO`` distinguish intent at the type
    level (and can diverge later without churning call sites).
    """

    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, str]) -> "PatientWriteDTO":
        """Build from any string mapping (e.g. ``request.form`` or parsed JSON)."""
        return cls(
            name=(data.get("name") or "").strip(),
            phone=(data.get("phone") or "").strip(),
            email=(data.get("email") or "").strip(),
            notes=(data.get("notes") or "").strip(),
        )


@dataclass(frozen=True)
class CreatePatientDTO(PatientWriteDTO):
    """Input to create a patient."""


@dataclass(frozen=True)
class UpdatePatientDTO(PatientWriteDTO):
    """Input to update an existing patient."""


@dataclass(frozen=True)
class PatientDTO:
    """A patient as exposed to callers — no ORM instance, no live session.

    ``phone_e164`` is the canonical dialable form; ``phone_display`` is the
    value to pre-fill an edit form (round-trips through phone normalization).
    """

    id: int
    clinic_id: int
    name: str
    country_code: str | None
    phone_national: str | None
    phone_e164: str | None
    phone_display: str
    email: str | None
    notes: str | None

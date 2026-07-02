"""Patient DTOs — the patient shapes exposed across layer boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PatientFormData:
    """Raw, unvalidated patient input as it arrives from a form or client.

    This is the *input* boundary: routes build it from the request, services
    validate it. Values are stripped of surrounding whitespace on construction.
    """

    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, str]) -> "PatientFormData":
        """Build from any string mapping (e.g. ``request.form``)."""
        return cls(
            name=(data.get("name") or "").strip(),
            phone=(data.get("phone") or "").strip(),
            email=(data.get("email") or "").strip(),
            notes=(data.get("notes") or "").strip(),
        )


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

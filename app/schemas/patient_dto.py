"""Patient DTOs — the patient shapes the service layer speaks.

These are the service's input/output language, independent of any transport. A
route builds a ``CreatePatientDTO`` from an HTML form; a future REST endpoint
would build the same DTO from a JSON body — the service neither knows nor cares
which. (The HTML-form-specific representation, ``PatientFormData``, lives in the
routes layer, not here.)

Naming: input DTOs are ``Create<X>DTO`` / ``Update<X>DTO``; the read-side shape
returned to callers is ``<X>DTO``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreatePatientDTO:
    """What the service needs to create a patient (raw, pre-validation)."""

    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""


@dataclass(frozen=True)
class UpdatePatientDTO:
    """What the service needs to update a patient (raw, pre-validation).

    A distinct type from ``CreatePatientDTO`` so create/update inputs can diverge
    later without touching call sites.
    """

    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""


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

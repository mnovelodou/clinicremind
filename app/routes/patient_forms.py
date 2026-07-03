"""HTTP form object for patient create/edit — a routes-layer concern.

``PatientFormData`` represents the fields as submitted through the HTML form (and
as re-rendered back into it). It is deliberately specific to the HTTP/HTML
delivery layer: it parses ``request.form`` and knows how to translate itself into
the transport-agnostic service DTOs (``CreatePatientDTO`` / ``UpdatePatientDTO``).

A different delivery mechanism (e.g. a JSON REST endpoint) would build those DTOs
directly and never touch this class — which is the whole point of keeping form
handling out of the service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.schemas.patient_dto import CreatePatientDTO, UpdatePatientDTO


@dataclass(frozen=True)
class PatientFormData:
    """Patient fields as submitted via the HTML form. Values are stripped."""

    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""

    @classmethod
    def from_form(cls, form: Mapping[str, str]) -> "PatientFormData":
        """Parse a submitted HTML form (``request.form``) into a form object."""
        return cls(
            name=(form.get("name") or "").strip(),
            phone=(form.get("phone") or "").strip(),
            email=(form.get("email") or "").strip(),
            notes=(form.get("notes") or "").strip(),
        )

    def to_create_dto(self) -> CreatePatientDTO:
        """Translate the form into the service's create-input DTO."""
        return CreatePatientDTO(
            name=self.name, phone=self.phone, email=self.email, notes=self.notes
        )

    def to_update_dto(self) -> UpdatePatientDTO:
        """Translate the form into the service's update-input DTO."""
        return UpdatePatientDTO(
            name=self.name, phone=self.phone, email=self.email, notes=self.notes
        )

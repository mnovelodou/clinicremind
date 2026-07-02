"""Persistence for patients — all patient SQLAlchemy queries live here."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Patient


class PatientRepository:
    """Clinic-scoped data access for ``Patient`` rows.

    Every read is filtered by ``clinic_id`` so a caller cannot accidentally
    reach across clinics — the scoping boundary is enforced in one place.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_clinic(self, clinic_id: int) -> list[Patient]:
        """All patients in a clinic, ordered by name."""
        return (
            self._session.query(Patient)
            .filter_by(clinic_id=clinic_id)
            .order_by(Patient.name)
            .all()
        )

    def get_for_clinic(self, clinic_id: int, patient_id: int) -> Patient | None:
        """A single patient by id, or None if it isn't in this clinic."""
        return (
            self._session.query(Patient)
            .filter_by(id=patient_id, clinic_id=clinic_id)
            .first()
        )

    def create(
        self,
        *,
        clinic_id: int,
        name: str,
        country_code: str | None,
        phone_national: str | None,
        email: str | None,
        notes: str | None,
    ) -> Patient:
        """Insert and commit a new patient, returning the persisted model."""
        patient = Patient(
            clinic_id=clinic_id,
            name=name,
            country_code=country_code,
            phone_national=phone_national,
            email=email,
            notes=notes,
        )
        self._session.add(patient)
        self._session.commit()
        return patient

    def save(self, patient: Patient) -> Patient:
        """Commit pending changes to an already-tracked patient."""
        self._session.commit()
        return patient

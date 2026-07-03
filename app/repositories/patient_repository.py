"""Persistence for patients — all patient SQLAlchemy queries live here."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Patient

# Safety cap so the list query is never unbounded. Real paginated/searchable
# listing is P2 (patient search); this just prevents an accidental full-table
# fetch in the P1 landing list.
DEFAULT_LIST_LIMIT = 100


class PatientRepository:
    """Clinic-scoped data access for ``Patient`` rows.

    Every read is filtered by ``clinic_id`` so a caller cannot accidentally
    reach across clinics — the scoping boundary is enforced in one place.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_clinic(
        self, clinic_id: int, *, limit: int = DEFAULT_LIST_LIMIT, offset: int = 0
    ) -> list[Patient]:
        """Patients in a clinic, ordered by name, bounded by ``limit``."""
        return (
            self._session.query(Patient)
            .filter_by(clinic_id=clinic_id)
            .order_by(Patient.name)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_for_clinic(self, clinic_id: int, patient_id: int) -> Patient | None:
        """A single patient by id, or None if it isn't in this clinic."""
        return (
            self._session.query(Patient)
            .filter_by(id=patient_id, clinic_id=clinic_id)
            .first()
        )

    def create(self, patient: Patient) -> Patient:
        """Insert and commit a new patient, returning the persisted model."""
        self._session.add(patient)
        self._session.commit()
        return patient

    def save(self, patient: Patient) -> Patient:
        """Commit pending changes to an already-tracked patient."""
        self._session.commit()
        return patient

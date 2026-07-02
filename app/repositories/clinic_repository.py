"""Persistence for clinics."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Clinic


class ClinicRepository:
    """Data access for ``Clinic`` rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_default(self) -> Clinic | None:
        """The default clinic (lowest id) — the single seeded clinic pre-Auth."""
        return self._session.query(Clinic).order_by(Clinic.id).first()

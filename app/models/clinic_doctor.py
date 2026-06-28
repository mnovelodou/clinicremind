"""ClinicDoctor — which clinics a doctor works at.

A doctor is a global identity (see ``Doctor``); this association records each
clinic the doctor works at. At most one row per (clinic, doctor) pair.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class ClinicDoctor(db.Model):
    __tablename__ = "clinic_doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("clinic_id", "doctor_id", name="uq_clinic_doctor"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ClinicDoctor clinic={self.clinic_id} doctor={self.doctor_id}>"

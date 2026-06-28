"""Patient — a clinic-wide contact record. No clinical/medical data.

Phone is stored twice: ``phone`` is the canonical E.164 value (with country
code) used for display, ICS, and later WhatsApp; ``phone_national`` is the
national significant number (digits only, no country code) and is the column
the front desk searches, so a patient can be found by local number without
typing the country code. Normalization logic lives in P1/P2.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Patient(db.Model):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Canonical E.164, e.g. "+5215512345678".
    phone: Mapped[str | None] = mapped_column(String(20))
    # National significant number, digits only, e.g. "5512345678" — searchable.
    phone_national: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(320))
    notes: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_patients_clinic_phone_national", "clinic_id", "phone_national"),
        Index("ix_patients_clinic_name", "clinic_id", "name"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Patient {self.id} {self.name!r}>"

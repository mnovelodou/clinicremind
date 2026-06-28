"""Doctor — a calendar owner, optionally linked to a user login.

A doctor is a global identity, not bound to a single clinic: the same doctor may
work at several clinics (one at a time). Which clinics a doctor works at is
recorded in ``clinic_doctors`` (see ``ClinicDoctor``). Appointments and grants
still carry both ``clinic_id`` and ``doctor_id`` to pin the clinic context.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable: a doctor may be a calendar owner without a login.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Doctor {self.id} {self.name!r}>"

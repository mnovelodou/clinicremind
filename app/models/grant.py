"""DoctorReceptionistGrant — which receptionist may act for which doctor.

A grant with ``revoked_at IS NULL`` is active. Revoking sets the timestamp
rather than deleting, preserving history. A partial unique index ensures at most
one active grant per (doctor, receptionist) pair.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class DoctorReceptionistGrant(db.Model):
    __tablename__ = "doctor_receptionist_grants"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    receptionist_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # At most one active grant per (doctor, receptionist).
        Index(
            "uq_active_grant",
            "doctor_id",
            "receptionist_user_id",
            unique=True,
            postgresql_where="revoked_at IS NULL",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<Grant doctor={self.doctor_id} "
            f"receptionist={self.receptionist_user_id} "
            f"active={self.revoked_at is None}>"
        )

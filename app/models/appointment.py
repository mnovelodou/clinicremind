"""Appointment — a patient booked with a doctor at a time, with a status.

``rescheduled`` marks an appointment whose time was moved to a replacement
appointment, preserving the original rather than mutating it in place.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class AppointmentStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rescheduled = "rescheduled"
    cancelled = "cancelled"
    no_show = "no_show"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status", native_enum=True),
        nullable=False,
        server_default=AppointmentStatus.pending.value,
    )
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
        # Calendar / day views: a doctor's appointments in a time range.
        Index("ix_appointments_clinic_doctor_start", "clinic_id", "doctor_id", "start_at"),
        # Patient history / next appointment, doctor-independent.
        Index("ix_appointments_patient_start", "patient_id", "start_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Appointment {self.id} {self.status.value} {self.start_at}>"

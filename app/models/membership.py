"""ClinicMember — links a user to a clinic with a role.

A user may hold more than one membership row in the same clinic (e.g. both
``admin`` and ``doctor``). ``super_admin`` is intentionally not a membership
role; it lives on ``users.is_super_admin``.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class MemberRole(enum.Enum):
    admin = "admin"
    receptionist = "receptionist"
    doctor = "doctor"


class ClinicMember(db.Model):
    __tablename__ = "clinic_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role", native_enum=True), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ClinicMember user={self.user_id} clinic={self.clinic_id} {self.role.value}>"

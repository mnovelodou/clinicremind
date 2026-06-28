"""Patient — a clinic-wide contact record. No clinical/medical data.

Phone is stored in two parts: ``country_code`` (numeric dialing code, e.g.
``"52"``) and ``phone_national`` (national significant number, digits only,
e.g. ``"5512345678"``). The canonical E.164 value is reconstructed when needed
as ``"+" + country_code + phone_national`` (display, ICS, later WhatsApp).
``phone_national`` is what the front desk searches, so a patient can be found by
local number without typing the country code. Numbers entered without a "+"
default to the clinic's ``default_country``. Normalization lives in P1/P2.

``name`` is searchable by any substring (e.g. "novelo" matches "Jose Miguel
Novelo Vargas") via a trigram GIN index; see the migration for the pg_trgm
extension.
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
    # Numeric dialing code without "+", e.g. "52". Combined with phone_national
    # to reconstruct the canonical E.164 number.
    country_code: Mapped[str | None] = mapped_column(String(4))
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
        # Trigram GIN index so `name ILIKE '%substr%'` (partial-name search,
        # clinic-scoped via the clinic_id filter) stays index-backed.
        Index(
            "ix_patients_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    @property
    def phone_e164(self) -> str | None:
        """Reconstruct the canonical E.164 number, or None if no phone stored."""
        if self.country_code and self.phone_national:
            return f"+{self.country_code}{self.phone_national}"
        return None

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Patient {self.id} {self.name!r}>"

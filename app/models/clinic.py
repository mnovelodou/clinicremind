"""Clinic — the top-level tenant entity. All data belongs to a clinic."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Clinic(db.Model):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    # IANA timezone name (e.g. "America/Mexico_City") for local-time rendering.
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    # ISO 3166-1 alpha-2 country code (e.g. "MX"). Default country used when
    # normalizing patient phone numbers entered without a leading "+".
    default_country: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Clinic {self.id} {self.name!r}>"

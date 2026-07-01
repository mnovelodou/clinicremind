"""Current-clinic resolution.

Until Auth (AU) lands, ClinicRemind runs against a hardcoded single-clinic
context: there is one clinic and every request operates on it. This module is
the single place that resolves "the current clinic", so when sessions/roles
arrive the swap to a user-derived clinic touches exactly one function.
"""

from __future__ import annotations

from werkzeug.exceptions import InternalServerError

from app.extensions import db
from app.models import Clinic


def current_clinic() -> Clinic:
    """Return the clinic the current request operates on.

    For now this is the single seeded clinic (lowest id). Raises if no clinic
    exists, since every front-desk route requires one — fail loud rather than
    silently scoping queries to nothing.
    """
    clinic = db.session.query(Clinic).order_by(Clinic.id).first()
    if clinic is None:
        raise InternalServerError(
            "No clinic exists. Run `flask seed` to create the sample clinic."
        )
    return clinic

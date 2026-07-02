"""Request-scoped context: which clinic are we operating on?

Cross-cutting concern used by every front-desk route. Until Auth (AU) lands
ClinicRemind runs against a single hardcoded clinic; this module is the one
place that resolves it, so the swap to a session/role-derived clinic touches
exactly one function. It returns a ``ClinicContext`` DTO, not the ORM model, so
routes never hold a live persistence object just to know their clinic.
"""

from __future__ import annotations

from werkzeug.exceptions import InternalServerError

from app.extensions import db
from app.mappers import clinic_mapper
from app.repositories.clinic_repository import ClinicRepository
from app.schemas.clinic_dto import ClinicContext


def current_clinic() -> ClinicContext:
    """Return the clinic the current request operates on.

    Raises if no clinic exists, since every front-desk route requires one —
    fail loud rather than silently scoping queries to nothing.
    """
    clinic = ClinicRepository(db.session).get_default()
    if clinic is None:
        raise InternalServerError(
            "No clinic exists. Run `flask seed` to create the sample clinic."
        )
    return clinic_mapper.to_context(clinic)

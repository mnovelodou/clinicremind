"""SQLAlchemy models for ClinicRemind.

Importing this package registers every table on ``db.metadata``. Alembic's
``env.py`` imports it so autogenerate and ``upgrade`` see the full schema, and
the app factory pulls models in transitively via the same shared ``db``.

One module per concern; this file re-exports every model so a single
``import app.models`` (or ``from app.models import *``) brings the whole schema
into scope.
"""

from __future__ import annotations

from .appointment import Appointment, AppointmentStatus
from .clinic import Clinic
from .clinic_doctor import ClinicDoctor
from .doctor import Doctor
from .grant import DoctorReceptionistGrant
from .membership import ClinicMember, MemberRole
from .patient import Patient
from .user import User

__all__ = [
    "Appointment",
    "AppointmentStatus",
    "Clinic",
    "ClinicDoctor",
    "ClinicMember",
    "Doctor",
    "DoctorReceptionistGrant",
    "MemberRole",
    "Patient",
    "User",
]

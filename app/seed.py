"""Seed sample data for local development and demos.

``flask seed`` populates the iteration-1 schema with a fixed, deterministic
dataset: one clinic, three doctors (some with a login, some without),
admin/doctor/receptionist logins, fifteen patients, a receptionist grant, and
thirty appointments spanning past/today/future across the full status
lifecycle.

Two safety properties:

- **Idempotent.** Every entity is looked up by a stable natural key and inserted
  only when absent, so re-running never duplicates rows or errors.
- **Production-guarded.** The command refuses to run whenever the environment is
  ``production`` (via ``APP_ENV``, or ``FLASK_ENV`` as a fallback). The guard is
  unconditional — there is no override flag — because a fixture command must
  never touch a real database.

Seeding is CLI-only; it is never wired into application startup.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext
from sqlalchemy import inspect as sa_inspect

from app.extensions import db
from app.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    ClinicDoctor,
    ClinicMember,
    Doctor,
    DoctorReceptionistGrant,
    MemberRole,
    Patient,
    User,
)
from app.security import hash_password

# Dev-only password shared by every seeded login. Safe to hardcode: the
# production guard prevents these accounts from ever being created in
# production, so this is fixture data, not a real credential.
DEV_PASSWORD = "password"

# --- Fixed dataset ---------------------------------------------------------
# All values are literals so a run on an empty database is fully reproducible.

CLINIC = {
    "name": "Sunrise Family Clinic",
    "phone": "+525555550100",
    "timezone": "America/Mexico_City",
    "default_country": "MX",
}

# (email, name, role) — each becomes a User plus a clinic_members row.
USERS = [
    ("admin@clinicremind.test", "Alicia Admin", MemberRole.admin),
    ("dr.reyes@clinicremind.test", "Dr. Rosa Reyes", MemberRole.doctor),
    ("reception@clinicremind.test", "Rita Reception", MemberRole.receptionist),
]

# (name, linked_user_email) — a None email means a calendar owner with no login.
DOCTORS = [
    ("Dr. Rosa Reyes", "dr.reyes@clinicremind.test"),
    ("Dr. Mateo Mendoza", None),
    ("Dr. Sofia Soto", None),
]

# The receptionist user acts for this doctor (an active grant).
GRANT_RECEPTIONIST_EMAIL = "reception@clinicremind.test"
GRANT_DOCTOR_NAME = "Dr. Mateo Mendoza"

# (name, country_code, phone_national, email) — phone is stored in two parts so
# the front desk can search by local number; country_code + phone_national
# reconstruct the canonical E.164 value.
PATIENTS = [
    ("Jose Miguel Novelo Vargas", "52", "9991110001", "jose.novelo@example.com"),
    ("Maria Fernanda Lopez Cruz", "52", "9991110002", "maria.lopez@example.com"),
    ("Carlos Eduardo Ramirez Díaz", "52", "9991110003", None),
    ("Ana Patricia Gomez Herrera", "52", "9991110004", "ana.gomez@example.com"),
    ("Luis Alberto Torres Mena", "52", "9991110005", None),
    ("Sofia Isabel Castro Pinto", "52", "9991110006", "sofia.castro@example.com"),
    ("Diego Armando Flores Rosas", "52", "9991110007", None),
    ("Valeria Gabriela Ruiz Solis", "52", "9991110008", "valeria.ruiz@example.com"),
    ("Fernando Javier Ortega Lara", "52", "9991110009", None),
    ("Gabriela Monserrat Vega Nava", "52", "9991110010", "gaby.vega@example.com"),
    ("Ricardo Antonio Peña Cano", "52", "9991110011", None),
    ("Daniela Alejandra Mora Ríos", "52", "9991110012", "dani.mora@example.com"),
    ("Emiliano Sebastian Cruz Gil", "52", "9991110013", None),
    ("Camila Renata Salas Bravo", "52", "9991110014", "camila.salas@example.com"),
    ("Andres Felipe Navarro Luna", "52", "9991110015", None),
]

# Day offsets from "today" used to place appointments — a fixed mix of past,
# today (0), and future so the calendar always has all three.
_DAY_OFFSETS = [-21, -14, -7, -3, -1, 0, 1, 2, 5, 9, 14, 21]
_NUM_APPOINTMENTS = 30


def is_production() -> bool:
    """True when the environment indicates production (``APP_ENV``/``FLASK_ENV``)."""
    env = os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or ""
    return env.strip().lower() == "production"


def _today_utc() -> datetime:
    """Midnight today (UTC), the anchor for appointment times."""
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _get_or_create(session, model, *, defaults=None, **lookup):
    """Return (instance, created) — find by ``lookup`` or insert with defaults.

    Existing rows are left untouched; this only fills gaps, which is what makes
    the whole seed idempotent.
    """
    instance = session.query(model).filter_by(**lookup).first()
    if instance is not None:
        return instance, False
    params = dict(lookup)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def seed_database(session) -> dict[str, int]:
    """Idempotently insert the fixed dataset; return per-table created counts.

    Does not commit — the caller owns the transaction boundary.
    """
    created: dict[str, int] = {
        "clinics": 0,
        "users": 0,
        "clinic_members": 0,
        "doctors": 0,
        "clinic_doctors": 0,
        "patients": 0,
        "grants": 0,
        "appointments": 0,
    }

    clinic, made = _get_or_create(session, Clinic, name=CLINIC["name"], defaults=CLINIC)
    created["clinics"] += int(made)

    # Users + their membership rows.
    users_by_email: dict[str, User] = {}
    for email, name, role in USERS:
        user, made = _get_or_create(
            session,
            User,
            email=email,
            defaults={"name": name, "password_hash": hash_password(DEV_PASSWORD)},
        )
        created["users"] += int(made)
        users_by_email[email] = user

        _, made = _get_or_create(
            session,
            ClinicMember,
            clinic_id=clinic.id,
            user_id=user.id,
            role=role,
        )
        created["clinic_members"] += int(made)

    # Doctors (optionally linked to a user) + clinic membership.
    doctors: list[Doctor] = []
    for name, linked_email in DOCTORS:
        user = users_by_email.get(linked_email) if linked_email else None
        doctor, made = _get_or_create(
            session,
            Doctor,
            name=name,
            defaults={"user_id": user.id if user else None},
        )
        created["doctors"] += int(made)
        doctors.append(doctor)

        _, made = _get_or_create(
            session,
            ClinicDoctor,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
        )
        created["clinic_doctors"] += int(made)

    # Receptionist → doctor grant (active: revoked_at is null).
    grant_doctor = next(d for d in doctors if d.name == GRANT_DOCTOR_NAME)
    grant_user = users_by_email[GRANT_RECEPTIONIST_EMAIL]
    _, made = _get_or_create(
        session,
        DoctorReceptionistGrant,
        doctor_id=grant_doctor.id,
        receptionist_user_id=grant_user.id,
        revoked_at=None,
        defaults={"clinic_id": clinic.id},
    )
    created["grants"] += int(made)

    # Patients.
    patients: list[Patient] = []
    for name, country_code, phone_national, email in PATIENTS:
        patient, made = _get_or_create(
            session,
            Patient,
            clinic_id=clinic.id,
            name=name,
            phone_national=phone_national,
            defaults={"country_code": country_code, "email": email},
        )
        created["patients"] += int(made)
        patients.append(patient)

    # Appointments — deterministic spread over doctors, patients, dates, and the
    # full status lifecycle. The natural key is (doctor, patient, start_at).
    statuses = list(AppointmentStatus)
    today = _today_utc()
    for i in range(_NUM_APPOINTMENTS):
        doctor = doctors[i % len(doctors)]
        patient = patients[i % len(patients)]
        offset = _DAY_OFFSETS[i % len(_DAY_OFFSETS)]
        hour = 8 + (i % 8)
        start_at = today + timedelta(days=offset, hours=hour)
        status = statuses[i % len(statuses)]
        _, made = _get_or_create(
            session,
            Appointment,
            doctor_id=doctor.id,
            patient_id=patient.id,
            start_at=start_at,
            defaults={
                "clinic_id": clinic.id,
                "end_at": start_at + timedelta(minutes=30),
                "status": status,
                "notes": None,
            },
        )
        created["appointments"] += int(made)

    return created


def _schema_present(session) -> bool:
    """True when the core tables exist (i.e. migrations have been applied)."""
    inspector = sa_inspect(session.get_bind())
    return "clinics" in inspector.get_table_names()


@click.command("seed")
@with_appcontext
def seed_command() -> None:
    """Populate the database with deterministic sample data (dev/demo only)."""
    if is_production():
        click.echo(
            "Refusing to seed: the environment is production "
            "(APP_ENV/FLASK_ENV=production). There is no override.",
            err=True,
        )
        raise SystemExit(1)

    if not _schema_present(db.session):
        click.echo(
            "Database schema not found. Run `alembic upgrade head` first.",
            err=True,
        )
        raise SystemExit(1)

    created = seed_database(db.session)
    db.session.commit()

    total = sum(created.values())
    if total == 0:
        click.echo("Already seeded — nothing to do (idempotent no-op).")
    else:
        summary = ", ".join(f"{n} {table}" for table, n in created.items() if n)
        click.echo(f"Seeded: {summary}.")
    click.echo(
        f"Dev logins (password '{DEV_PASSWORD}'): "
        + ", ".join(email for email, _, _ in USERS)
    )

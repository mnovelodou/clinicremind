"""Patient create/edit flows (patient-management capability, P1).

Patients are clinic-wide contact records — name, phone, email, notes — with no
clinical data. These routes run against the hardcoded ``current_clinic()``
context and scope every query to that clinic. Search (P2), detail/history (P3),
and deletion are out of scope here.

The create and edit pages share one form template. Submissions are HTMX posts:
on success the server replies with an ``HX-Redirect`` header so the browser
navigates to the patient list; on validation failure it re-renders the form
fragment with per-field errors and the user's input preserved.
"""

from __future__ import annotations

import re
from typing import Mapping

from flask import Blueprint, abort, make_response, render_template, request, url_for

from app.clinic_context import current_clinic
from app.extensions import db
from app.models import Patient
from app.phone import format_phone_input, normalize_phone

bp = Blueprint("patients", __name__, url_prefix="/patients")

# Pragmatic email shape check — not full RFC validation, just enough to catch
# obvious typos. Stricter validation can come with a real verification flow.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_patient_form(
    form: Mapping[str, str], default_country: str | None
) -> tuple[dict, dict, dict]:
    """Validate and normalize submitted patient fields.

    Returns ``(fields, values, errors)``:
    - ``fields``: persistence-ready kwargs for ``Patient`` (normalized phone).
    - ``values``: the raw input echoed back for re-rendering the form.
    - ``errors``: field name → message; empty when the input is valid.
    """
    name = (form.get("name") or "").strip()
    phone_raw = (form.get("phone") or "").strip()
    email = (form.get("email") or "").strip()
    notes = (form.get("notes") or "").strip()

    errors: dict[str, str] = {}
    if not name:
        errors["name"] = "Name is required."

    country_code, phone_national = normalize_phone(phone_raw, default_country)
    if phone_raw and phone_national is None:
        errors["phone"] = "Enter a valid phone number."

    if email and not _EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."

    fields = {
        "name": name,
        "country_code": country_code,
        "phone_national": phone_national,
        "email": email or None,
        "notes": notes or None,
    }
    values = {"name": name, "phone": phone_raw, "email": email, "notes": notes}
    return fields, values, errors


def _redirect_to_list():
    """HTMX-friendly redirect: empty body + ``HX-Redirect`` to the list."""
    resp = make_response("")
    resp.headers["HX-Redirect"] = url_for("patients.list_patients")
    return resp


@bp.get("/")
def list_patients():
    """List the current clinic's patients (create/edit landing surface)."""
    clinic = current_clinic()
    patients = (
        db.session.query(Patient)
        .filter_by(clinic_id=clinic.id)
        .order_by(Patient.name)
        .all()
    )
    return render_template("patients/list.html", patients=patients)


@bp.get("/new")
def new():
    """Serve the empty create form."""
    return render_template(
        "patients/form.html",
        title="New patient",
        action=url_for("patients.create"),
        values={"name": "", "phone": "", "email": "", "notes": ""},
        errors={},
    )


@bp.post("/")
def create():
    """Normalize, validate, and insert a patient scoped to the current clinic."""
    clinic = current_clinic()
    fields, values, errors = validate_patient_form(
        request.form, clinic.default_country
    )
    if errors:
        return (
            render_template(
                "patients/_form.html",
                action=url_for("patients.create"),
                values=values,
                errors=errors,
            ),
            200,
        )

    db.session.add(Patient(clinic_id=clinic.id, **fields))
    db.session.commit()
    return _redirect_to_list()


def _get_clinic_patient(patient_id: int) -> Patient:
    """Load a patient that belongs to the current clinic, else 404."""
    clinic = current_clinic()
    patient = (
        db.session.query(Patient)
        .filter_by(id=patient_id, clinic_id=clinic.id)
        .first()
    )
    if patient is None:
        abort(404)
    return patient


@bp.get("/<int:patient_id>/edit")
def edit(patient_id: int):
    """Serve the edit form pre-filled with the patient's current values."""
    patient = _get_clinic_patient(patient_id)
    values = {
        "name": patient.name,
        "phone": format_phone_input(patient.country_code, patient.phone_national),
        "email": patient.email or "",
        "notes": patient.notes or "",
    }
    return render_template(
        "patients/form.html",
        title="Edit patient",
        action=url_for("patients.update", patient_id=patient.id),
        values=values,
        errors={},
    )


@bp.post("/<int:patient_id>")
def update(patient_id: int):
    """Re-normalize, re-validate, and persist changes to an existing patient."""
    patient = _get_clinic_patient(patient_id)
    fields, values, errors = validate_patient_form(
        request.form, current_clinic().default_country
    )
    if errors:
        return (
            render_template(
                "patients/_form.html",
                action=url_for("patients.update", patient_id=patient.id),
                values=values,
                errors=errors,
            ),
            200,
        )

    patient.name = fields["name"]
    patient.country_code = fields["country_code"]
    patient.phone_national = fields["phone_national"]
    patient.email = fields["email"]
    patient.notes = fields["notes"]
    db.session.commit()
    return _redirect_to_list()

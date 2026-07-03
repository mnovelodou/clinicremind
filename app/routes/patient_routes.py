"""Patient create/edit routes (patient-management capability, P1).

Controller only: parse the request into a ``PatientFormData``, translate it into
the service's input DTO (``CreatePatientDTO`` / ``UpdatePatientDTO``), resolve the
current clinic, delegate to ``PatientService``, and turn the result — a
``PatientDTO`` or a domain exception — into a response. No business logic, no
queries here. ``PatientFormData`` is the HTML-form representation and never
crosses into the service.

Submissions are HTMX posts: on success the server replies with an
``HX-Redirect`` header so the browser navigates to the patient list; on
validation failure it re-renders the form fragment with per-field errors and the
user's input preserved.
"""

from __future__ import annotations

from flask import Blueprint, abort, make_response, render_template, request, url_for

from app.context import current_clinic
from app.extensions import db
from app.repositories.patient_repository import PatientRepository
from app.routes.patient_forms import PatientFormData
from app.services.exceptions import PatientNotFound, ValidationError
from app.services.patient_service import PatientService

bp = Blueprint("patients", __name__, url_prefix="/patients")


def _service() -> PatientService:
    """Wire a service to the request-scoped session."""
    return PatientService(PatientRepository(db.session))


def _redirect_to_list():
    """HTMX-friendly redirect: empty body + ``HX-Redirect`` to the list."""
    resp = make_response("")
    resp.headers["HX-Redirect"] = url_for("patients.list_patients")
    return resp


@bp.get("/")
def list_patients():
    """List the current clinic's patients (create/edit landing surface)."""
    clinic = current_clinic()
    patients = _service().list_for_clinic(clinic.id)
    return render_template("patients/list.html", patients=patients)


@bp.get("/new")
def new():
    """Serve the empty create form."""
    return render_template(
        "patients/form.html",
        title="New patient",
        action=url_for("patients.create"),
        values=PatientFormData(),
        errors={},
    )


@bp.post("/")
def create():
    """Create a patient scoped to the current clinic."""
    clinic = current_clinic()
    form = PatientFormData.from_form(request.form)
    try:
        _service().create(clinic.id, form.to_create_dto(), clinic.default_country)
    except ValidationError as exc:
        return (
            render_template(
                "patients/_form.html",
                action=url_for("patients.create"),
                values=form,
                errors=exc.errors,
            ),
            200,
        )
    return _redirect_to_list()


@bp.get("/<int:patient_id>/edit")
def edit(patient_id: int):
    """Serve the edit form pre-filled with the patient's current values."""
    clinic = current_clinic()
    try:
        patient = _service().get_for_edit(clinic.id, patient_id)
    except PatientNotFound:
        abort(404)
    values = PatientFormData(
        name=patient.name,
        phone=patient.phone_display,
        email=patient.email or "",
        notes=patient.notes or "",
    )
    return render_template(
        "patients/form.html",
        title="Edit patient",
        action=url_for("patients.update", patient_id=patient.id),
        values=values,
        errors={},
    )


@bp.post("/<int:patient_id>")
def update(patient_id: int):
    """Persist changes to an existing clinic patient."""
    clinic = current_clinic()
    form = PatientFormData.from_form(request.form)
    try:
        _service().update(
            clinic.id, patient_id, form.to_update_dto(), clinic.default_country
        )
    except PatientNotFound:
        abort(404)
    except ValidationError as exc:
        return (
            render_template(
                "patients/_form.html",
                action=url_for("patients.update", patient_id=patient_id),
                values=form,
                errors=exc.errors,
            ),
            200,
        )
    return _redirect_to_list()

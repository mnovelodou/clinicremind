"""Domain exceptions raised by services.

These are transport-agnostic: they describe *what* went wrong in business terms,
leaving each delivery layer to decide how to present it (a route maps
``PatientNotFound`` to HTTP 404, ``ValidationError`` to a re-rendered form).
"""

from __future__ import annotations


class ValidationError(Exception):
    """Submitted input failed validation.

    ``errors`` maps field name → human-readable message.
    """

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Input failed validation")
        self.errors = errors


class PatientNotFound(Exception):
    """No patient with the given id exists in the current clinic."""

    def __init__(self, patient_id: int) -> None:
        super().__init__(f"Patient {patient_id} not found in this clinic")
        self.patient_id = patient_id


class PersistenceError(Exception):
    """A repository/database operation failed.

    Services raise this after catching a low-level ``SQLAlchemyError`` so callers
    depend on a domain-level failure, not on SQLAlchemy. The original error is
    kept as ``__cause__`` for logging.
    """

    def __init__(self, message: str = "A database error occurred") -> None:
        super().__init__(message)

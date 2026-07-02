"""Clinic DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClinicContext:
    """The current clinic as seen by the rest of the app.

    A DTO rather than the ``Clinic`` ORM model so routes and services never hold
    a live persistence object just to know which clinic they operate on. Until
    Auth lands this is the single seeded clinic; see ``app.context``.
    """

    id: int
    name: str
    timezone: str
    default_country: str

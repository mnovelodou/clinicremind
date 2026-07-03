"""Services — business logic / use cases.

A service orchestrates repositories and mappers to carry out a use case. It
accepts DTOs (or primitives) and returns DTOs — never SQLAlchemy models — and
raises domain exceptions (see ``app.services.exceptions``) instead of producing
HTTP responses. This is the reusable core: any delivery layer (HTMX, a JSON API,
a CLI, another service) can call it. See docs/ARCHITECTURE.md.
"""

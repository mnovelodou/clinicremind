"""Data transfer objects (DTOs).

Plain, framework-free dataclasses that cross layer boundaries. Services accept
and return these — never SQLAlchemy models — so business logic stays decoupled
from persistence and can be reused by any delivery mechanism (HTMX today, a
JSON API or another service tomorrow). See docs/ARCHITECTURE.md.
"""

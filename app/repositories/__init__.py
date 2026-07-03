"""Repositories — the only layer that issues SQLAlchemy queries.

A repository owns persistence for one aggregate. It accepts and returns ORM
models (models may be exposed *to* services here), keeping raw query construction
out of services and routes. Swapping the storage engine, or moving this repo to
another service, is contained to this layer. See docs/ARCHITECTURE.md.
"""

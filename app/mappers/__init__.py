"""Mappers — convert between SQLAlchemy models and DTOs.

The only place that knows both a model's shape and its DTO's shape. Keeping the
translation here means services depend on DTOs, repositories depend on models,
and neither has to know the other's representation. See docs/ARCHITECTURE.md.
"""

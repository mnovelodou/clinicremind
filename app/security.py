"""Password hashing helpers (bcrypt).

Shared by the seed command and, later, the auth flow (AU1). Passwords are hashed
with bcrypt before storage; the plaintext is never persisted. A bcrypt hash is a
60-character string, which fits ``users.password_hash`` (``String(255)``).
"""

from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of ``plain``, suitable for ``users.password_hash``."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if ``plain`` matches the stored bcrypt ``hashed`` value."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

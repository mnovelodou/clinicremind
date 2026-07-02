"""Phone-number normalization for patient contact records.

The schema stores a phone as two digits-only parts — ``country_code`` (numeric
dialing code, e.g. ``"52"``) and ``phone_national`` (national significant
number, e.g. ``"5512345678"``) — and reconstructs the canonical E.164 value on
demand (see ``Patient.phone_e164``). This module turns free-form front-desk
input into those two parts and back again.

Rules (P1):
- A leading ``+`` or international ``00`` prefix means the number carries its own
  country code; the rest is split into country code + national number using the
  set of dialing codes we know about (longest match wins).
- Otherwise the number is treated as local and the country code defaults to the
  clinic's ``default_country``.
- All formatting characters (spaces, dashes, parentheses) are stripped.
- Blank input yields ``(None, None)``.

This is deliberately lightweight — no ``phonenumbers`` dependency. It honours the
digits-only storage contract without validating real-world number plans; P2 can
swap in stricter validation behind the same interface.
"""

from __future__ import annotations

import re

# ISO 3166-1 alpha-2 → numeric dialing code (digits only). Covers the seeded
# clinic (MX) plus common countries the front desk is likely to encounter. Add
# entries here as new clinics onboard.
ISO_TO_DIALING_CODE: dict[str, str] = {
    "MX": "52",
    "US": "1",
    "CA": "1",
    "GT": "502",
    "BZ": "501",
    "ES": "34",
    "AR": "54",
    "CO": "57",
    "BR": "55",
    "GB": "44",
}

# The dialing codes we can recognise at the front of an international number.
_KNOWN_DIALING_CODES = set(ISO_TO_DIALING_CODE.values())

_NON_DIGITS = re.compile(r"\D")


def dialing_code_for(iso_country: str | None) -> str | None:
    """Return the numeric dialing code for an ISO alpha-2 country, or None."""
    if not iso_country:
        return None
    return ISO_TO_DIALING_CODE.get(iso_country.upper())


def _split_international(digits: str) -> tuple[str | None, str | None]:
    """Split a digits-only international number into (country_code, national).

    Matches the longest known dialing-code prefix (up to three digits). When no
    known code matches, falls back gracefully: the country code is left null and
    all digits are kept as the national number rather than raising.
    """
    for length in (3, 2, 1):
        if digits[:length] in _KNOWN_DIALING_CODES:
            return digits[:length], (digits[length:] or None)
    return None, (digits or None)


def normalize_phone(
    raw: str | None, default_country: str | None
) -> tuple[str | None, str | None]:
    """Normalize free-form input into ``(country_code, phone_national)``.

    ``default_country`` is the clinic's ISO alpha-2 country, used as the country
    code when the input has no international prefix.
    """
    if raw is None:
        return None, None
    s = raw.strip()
    if not s:
        return None, None

    digits = _NON_DIGITS.sub("", s)
    if not digits:
        return None, None

    if s.startswith("+"):
        return _split_international(digits)
    if s.startswith("00"):
        # International access prefix; drop it and split the remainder.
        return _split_international(digits[2:])

    # Local number — assume the clinic's default country.
    return dialing_code_for(default_country), digits


def format_phone_input(country_code: str | None, phone_national: str | None) -> str:
    """Render stored parts back into a display value for pre-filling a form.

    Round-trips with ``normalize_phone``: feeding the result back in reproduces
    the same ``(country_code, phone_national)`` pair.
    """
    if country_code and phone_national:
        return f"+{country_code}{phone_national}"
    if phone_national:
        return phone_national
    return ""

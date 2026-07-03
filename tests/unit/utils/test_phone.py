"""Unit tests for phone normalization (patient-management capability).

Pure functions — no database. Covers the P1 normalization contract: local
numbers default to the clinic country, international-prefixed numbers keep their
own country code, formatting is stripped, and blanks yield nulls.
"""

from __future__ import annotations

import pytest

from app.utils.phone import format_phone_input, normalize_phone


def test_local_number_defaults_to_clinic_country():
    assert normalize_phone("55 1234 5678", "MX") == ("52", "5512345678")


def test_international_prefix_keeps_country_code():
    assert normalize_phone("+1 (415) 555-0100", "MX") == ("1", "4155550100")


def test_international_prefix_longest_match_wins():
    # "52" must win over "5" so a Mexican number is not mis-split.
    assert normalize_phone("+52 55 1234 5678", "US") == ("52", "5512345678")


def test_double_zero_prefix_is_international():
    assert normalize_phone("0052 5512345678", "US") == ("52", "5512345678")


def test_formatting_characters_are_stripped():
    cc, national = normalize_phone(" (55) 1234-5678 ", "MX")
    assert cc == "52"
    assert national == "5512345678"
    assert national.isdigit()


@pytest.mark.parametrize("blank", [None, "", "   ", "()-"])
def test_blank_phone_yields_nulls(blank):
    assert normalize_phone(blank, "MX") == (None, None)


def test_unmapped_default_country_leaves_code_null():
    # A country we don't know a dialing code for still stores the digits.
    assert normalize_phone("5512345678", "ZZ") == (None, "5512345678")


def test_unknown_international_code_falls_back_gracefully():
    # +999 is not a known code — no crash; digits kept as national.
    assert normalize_phone("+999 12345", "MX") == (None, "99912345")


def test_format_round_trips_with_normalize():
    display = format_phone_input("52", "5512345678")
    assert display == "+525512345678"
    assert normalize_phone(display, "US") == ("52", "5512345678")


def test_format_blank_when_no_number():
    assert format_phone_input(None, None) == ""

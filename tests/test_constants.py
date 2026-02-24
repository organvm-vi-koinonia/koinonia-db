"""Tests for koinonia_db.constants — organ map and difficulty ordering."""

from __future__ import annotations

import re

import pytest

from koinonia_db.constants import ORGAN_MAP, DIFFICULTY_ORDER


# ---------------------------------------------------------------------------
# ORGAN_MAP
# ---------------------------------------------------------------------------


class TestOrganMap:
    def test_has_exactly_eight_entries(self):
        """ORGAN_MAP should contain exactly 8 organs."""
        assert len(ORGAN_MAP) == 8

    def test_all_roman_numeral_keys_present(self):
        """All eight organ keys (I through VIII) should exist."""
        expected_keys = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"}
        assert set(ORGAN_MAP.keys()) == expected_keys

    def test_values_follow_roman_name_pattern(self):
        """Every value should match the pattern 'roman-name' (lowercase roman numeral, hyphen, name)."""
        pattern = re.compile(r"^[ivx]+-[a-z]+$")
        for key, value in ORGAN_MAP.items():
            assert pattern.match(value), (
                f"ORGAN_MAP['{key}'] = '{value}' does not match expected pattern 'roman-name'"
            )

    def test_specific_organ_values(self):
        """Spot-check specific organ mappings."""
        assert ORGAN_MAP["I"] == "i-theoria"
        assert ORGAN_MAP["II"] == "ii-poiesis"
        assert ORGAN_MAP["III"] == "iii-ergon"
        assert ORGAN_MAP["IV"] == "iv-taxis"
        assert ORGAN_MAP["V"] == "v-logos"
        assert ORGAN_MAP["VI"] == "vi-koinonia"
        assert ORGAN_MAP["VII"] == "vii-kerygma"
        assert ORGAN_MAP["VIII"] == "viii-meta"

    def test_values_are_unique(self):
        """No two organs should share the same slug value."""
        values = list(ORGAN_MAP.values())
        assert len(values) == len(set(values))

    def test_is_plain_dict(self):
        """ORGAN_MAP should be a plain dict (not some special subclass)."""
        assert type(ORGAN_MAP) is dict


# ---------------------------------------------------------------------------
# DIFFICULTY_ORDER
# ---------------------------------------------------------------------------


class TestDifficultyOrder:
    def test_has_three_levels(self):
        """DIFFICULTY_ORDER should have exactly 3 difficulty levels."""
        assert len(DIFFICULTY_ORDER) == 3

    def test_expected_keys(self):
        """The three expected difficulty keys should be present."""
        assert set(DIFFICULTY_ORDER.keys()) == {"beginner", "intermediate", "advanced"}

    def test_correct_ordering(self):
        """Difficulty levels should be ordered beginner(0) < intermediate(1) < advanced(2)."""
        assert DIFFICULTY_ORDER["beginner"] == 0
        assert DIFFICULTY_ORDER["intermediate"] == 1
        assert DIFFICULTY_ORDER["advanced"] == 2

    def test_order_is_monotonically_increasing(self):
        """The numeric values should increase from beginner to advanced."""
        assert DIFFICULTY_ORDER["beginner"] < DIFFICULTY_ORDER["intermediate"]
        assert DIFFICULTY_ORDER["intermediate"] < DIFFICULTY_ORDER["advanced"]

    def test_is_plain_dict(self):
        """DIFFICULTY_ORDER should be a plain dict."""
        assert type(DIFFICULTY_ORDER) is dict

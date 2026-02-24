"""Shared constants for ORGAN-VI repos."""

from __future__ import annotations

# Mapping of organ Roman numeral codes to their slug identifiers
ORGAN_MAP: dict[str, str] = {
    "I": "i-theoria",
    "II": "ii-poiesis",
    "III": "iii-ergon",
    "IV": "iv-taxis",
    "V": "v-logos",
    "VI": "vi-koinonia",
    "VII": "vii-kerygma",
    "VIII": "viii-meta",
}

DIFFICULTY_ORDER: dict[str, int] = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}

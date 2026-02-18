"""Tests for seed data files — verifies JSON structure and content."""

from __future__ import annotations

import json
from pathlib import Path

SEED_DIR = Path(__file__).parent.parent / "seed"


def test_taxonomy_json_loads():
    data = json.loads((SEED_DIR / "taxonomy.json").read_text())
    assert "nodes" in data
    nodes = data["nodes"]
    assert len(nodes) == 8  # 8 organs
    for node in nodes:
        assert "slug" in node
        assert "label" in node
        assert "children" in node
        assert len(node["children"]) >= 3


def test_taxonomy_has_all_organs():
    data = json.loads((SEED_DIR / "taxonomy.json").read_text())
    slugs = {n["slug"] for n in data["nodes"]}
    expected = {
        "i-theoria", "ii-poiesis", "iii-ergon", "iv-taxis",
        "v-logos", "vi-koinonia", "vii-kerygma", "viii-meta",
    }
    assert slugs == expected


def test_taxonomy_total_nodes():
    data = json.loads((SEED_DIR / "taxonomy.json").read_text())
    total = len(data["nodes"])
    for node in data["nodes"]:
        total += len(node["children"])
    assert total >= 40  # 8 roots + 32+ children


def test_curricula_json_loads():
    data = json.loads((SEED_DIR / "curricula.json").read_text())
    assert "curricula" in data
    curricula = data["curricula"]
    assert len(curricula) == 3


def test_curricula_have_sessions():
    data = json.loads((SEED_DIR / "curricula.json").read_text())
    for c in data["curricula"]:
        assert "sessions" in c
        assert len(c["sessions"]) == c["duration_weeks"]
        for s in c["sessions"]:
            assert "week" in s
            assert "title" in s
            assert "readings" in s
            assert "questions" in s


def test_reading_lists_json_loads():
    data = json.loads((SEED_DIR / "reading_lists.json").read_text())
    assert "entries" in data
    entries = data["entries"]
    assert len(entries) >= 30
    for entry in entries:
        assert "key" in entry
        assert "title" in entry
        assert "author" in entry


def test_sample_sessions_json_loads():
    data = json.loads((SEED_DIR / "sample_sessions.json").read_text())
    assert "sessions" in data
    sessions = data["sessions"]
    assert len(sessions) == 2
    for session in sessions:
        assert "title" in session
        assert "segments" in session
        assert len(session["segments"]) >= 3
        assert "participants" in session


def test_reading_keys_match_curricula():
    """Every reading key referenced in curricula should exist in reading_lists."""
    curricula = json.loads((SEED_DIR / "curricula.json").read_text())
    readings = json.loads((SEED_DIR / "reading_lists.json").read_text())
    available_keys = {e["key"] for e in readings["entries"]}

    referenced_keys = set()
    for c in curricula["curricula"]:
        for s in c["sessions"]:
            referenced_keys.update(s["readings"])

    missing = referenced_keys - available_keys
    assert not missing, f"Missing reading entries: {missing}"

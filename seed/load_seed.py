#!/usr/bin/env python3
"""Load seed data into the koinonia-db Postgres database.

Usage:
    DATABASE_URL="postgresql://..." python seed/load_seed.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import psycopg

SEED_DIR = Path(__file__).parent


def get_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return url


def load_json(name: str) -> dict:
    return json.loads((SEED_DIR / name).read_text())


def seed_taxonomy(cur: psycopg.Cursor) -> int:
    data = load_json("taxonomy.json")
    count = 0
    for node in data["nodes"]:
        cur.execute(
            """INSERT INTO salons.taxonomy_nodes (slug, label, organ_id, description)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (slug) DO NOTHING
               RETURNING id""",
            (node["slug"], node["label"], node.get("organ_id"), node.get("description", "")),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute("SELECT id FROM salons.taxonomy_nodes WHERE slug = %s", (node["slug"],))
            row = cur.fetchone()
        parent_id = row[0]
        count += 1
        for child in node.get("children", []):
            cur.execute(
                """INSERT INTO salons.taxonomy_nodes (slug, label, parent_id, description)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (slug) DO NOTHING""",
                (child["slug"], child["label"], parent_id, child.get("description", "")),
            )
            count += 1
    return count


def seed_sessions(cur: psycopg.Cursor) -> int:
    data = load_json("sample_sessions.json")
    count = 0
    for session in data["sessions"]:
        cur.execute(
            """INSERT INTO salons.sessions (title, date, format, facilitator, notes, organ_tags)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (
                session["title"],
                session["date"],
                session.get("format", "deep_dive"),
                session.get("facilitator"),
                session.get("notes", ""),
                session.get("organ_tags", []),
            ),
        )
        session_id = cur.fetchone()[0]
        count += 1

        for p in session.get("participants", []):
            cur.execute(
                """INSERT INTO salons.participants (session_id, name, role, consent_given)
                   VALUES (%s, %s, %s, %s)""",
                (session_id, p["name"], p.get("role", "participant"), p.get("consent_given", False)),
            )
            count += 1

        for seg in session.get("segments", []):
            cur.execute(
                """INSERT INTO salons.segments
                   (session_id, speaker, text, start_seconds, end_seconds, confidence)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    session_id,
                    seg["speaker"],
                    seg["text"],
                    seg["start_seconds"],
                    seg["end_seconds"],
                    seg.get("confidence", 0.0),
                ),
            )
            count += 1
    return count


def seed_reading_entries(cur: psycopg.Cursor) -> dict[str, int]:
    """Load reading entries and return a key->id map."""
    data = load_json("reading_lists.json")
    key_map: dict[str, int] = {}
    for entry in data["entries"]:
        cur.execute(
            """INSERT INTO reading.entries (title, author, source_type, url, pages, difficulty, organ_tags)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (
                entry["title"],
                entry["author"],
                entry.get("source_type", "book"),
                entry.get("url"),
                entry.get("pages"),
                entry.get("difficulty", "intermediate"),
                entry.get("organ_tags", []),
            ),
        )
        key_map[entry["key"]] = cur.fetchone()[0]
    return key_map


def seed_curricula(cur: psycopg.Cursor, entry_key_map: dict[str, int]) -> int:
    data = load_json("curricula.json")
    count = 0
    for c in data["curricula"]:
        cur.execute(
            """INSERT INTO reading.curricula (title, theme, organ_focus, duration_weeks, description)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (c["title"], c.get("theme", "general"), c.get("organ_focus"), c["duration_weeks"], c.get("description", "")),
        )
        curriculum_id = cur.fetchone()[0]
        count += 1

        for s in c["sessions"]:
            cur.execute(
                """INSERT INTO reading.sessions (curriculum_id, week, title)
                   VALUES (%s, %s, %s)
                   RETURNING id""",
                (curriculum_id, s["week"], s["title"]),
            )
            session_id = cur.fetchone()[0]
            count += 1

            # Link readings to session
            for reading_key in s.get("readings", []):
                entry_id = entry_key_map.get(reading_key)
                if entry_id:
                    cur.execute(
                        """INSERT INTO reading.session_entries (session_id, entry_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (session_id, entry_id),
                    )

            # Add discussion questions
            for q in s.get("questions", []):
                cur.execute(
                    """INSERT INTO reading.discussion_questions (session_id, question_text, category)
                       VALUES (%s, %s, %s)""",
                    (session_id, q, "deep_dive"),
                )
                count += 1

            # Add guide if activities present
            activities = s.get("activities", [])
            if activities:
                cur.execute(
                    """INSERT INTO reading.guides
                       (session_id, opening_questions, deep_dive_questions, activities, closing_reflection)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        session_id,
                        s.get("questions", [])[:2],
                        s.get("questions", [])[2:],
                        activities,
                        "",
                    ),
                )
                count += 1
    return count


def main() -> None:
    url = get_url()
    print(f"Connecting to database...")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            # Check if already seeded
            cur.execute("SELECT count(*) FROM salons.taxonomy_nodes")
            existing = cur.fetchone()[0]
            if existing > 0:
                print(f"Database already has {existing} taxonomy nodes. Skipping seed.")
                print("To re-seed, truncate the tables first.")
                return

            print("Loading taxonomy...")
            tax_count = seed_taxonomy(cur)
            print(f"  -> {tax_count} taxonomy nodes")

            print("Loading salon sessions...")
            session_count = seed_sessions(cur)
            print(f"  -> {session_count} session records (sessions + participants + segments)")

            print("Loading reading entries...")
            entry_map = seed_reading_entries(cur)
            print(f"  -> {len(entry_map)} reading entries")

            print("Loading curricula...")
            curr_count = seed_curricula(cur, entry_map)
            print(f"  -> {curr_count} curriculum records (curricula + sessions + questions + guides)")

        conn.commit()

    total = tax_count + session_count + len(entry_map) + curr_count
    print(f"\nSeed complete: {total} total records loaded.")


if __name__ == "__main__":
    main()

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
        # Use title+date as a natural key for idempotency
        cur.execute(
            "SELECT id FROM salons.sessions WHERE title = %s AND date = %s",
            (session["title"], session["date"]),
        )
        existing = cur.fetchone()
        if existing:
            count += 1
            continue

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
    """Load reading entries and return a key->id map. Skips duplicates by title+author."""
    data = load_json("reading_lists.json")
    key_map: dict[str, int] = {}
    for entry in data["entries"]:
        # Check if already exists (title+author as natural key)
        cur.execute(
            "SELECT id FROM reading.entries WHERE title = %s AND author = %s",
            (entry["title"], entry["author"]),
        )
        existing = cur.fetchone()
        if existing:
            key_map[entry["key"]] = existing[0]
            continue

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
        # Skip if curriculum already exists (title as natural key)
        cur.execute(
            "SELECT id FROM reading.curricula WHERE title = %s",
            (c["title"],),
        )
        existing = cur.fetchone()
        if existing:
            count += 1
            continue

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


def seed_community(cur: psycopg.Cursor) -> int:
    """Seed community events, contributors, and contributions from community.json."""
    data = load_json("community.json")
    count = 0

    # Events — idempotent on title+date
    for event in data["events"]:
        cur.execute(
            "SELECT id FROM community.events WHERE title = %s AND date = %s",
            (event["title"], event["date"]),
        )
        if cur.fetchone():
            count += 1
            continue
        cur.execute(
            """INSERT INTO community.events
               (type, title, date, description, format, capacity, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                event["type"],
                event["title"],
                event["date"],
                event.get("description", ""),
                event.get("format", "virtual"),
                event.get("capacity"),
                event.get("status", "planned"),
            ),
        )
        count += 1

    # Contributors + contributions — idempotent on github_handle
    for contributor in data["contributors"]:
        cur.execute(
            "SELECT id FROM community.contributors WHERE github_handle = %s",
            (contributor["github_handle"],),
        )
        existing = cur.fetchone()
        if existing:
            contributor_id = existing[0]
        else:
            cur.execute(
                """INSERT INTO community.contributors
                   (github_handle, name, organs_active, first_contribution_date)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id""",
                (
                    contributor["github_handle"],
                    contributor["name"],
                    contributor.get("organs_active", []),
                    contributor.get("first_contribution_date"),
                ),
            )
            contributor_id = cur.fetchone()[0]
        count += 1

        for c in contributor.get("contributions", []):
            # Idempotent on contributor_id+repo+date
            cur.execute(
                """SELECT id FROM community.contributions
                   WHERE contributor_id = %s AND repo = %s AND date = %s""",
                (contributor_id, c["repo"], c["date"]),
            )
            if cur.fetchone():
                count += 1
                continue
            cur.execute(
                """INSERT INTO community.contributions
                   (contributor_id, repo, type, date, description)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    contributor_id,
                    c["repo"],
                    c["type"],
                    c["date"],
                    c.get("description", ""),
                ),
            )
            count += 1

    return count


def _table_count(cur: psycopg.Cursor, table: str) -> int:
    cur.execute(f"SELECT count(*) FROM {table}")
    return cur.fetchone()[0]


def main() -> None:
    url = get_url()
    print("Connecting to database...")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            # Seed each table independently — partial runs can resume safely
            print("Loading taxonomy...")
            tax_count = seed_taxonomy(cur)
            print(f"  -> {tax_count} taxonomy nodes (total: {_table_count(cur, 'salons.taxonomy_nodes')})")

            print("Loading salon sessions...")
            session_count = seed_sessions(cur)
            print(f"  -> {session_count} session records")

            print("Loading reading entries...")
            entry_map = seed_reading_entries(cur)
            print(f"  -> {len(entry_map)} reading entries")

            print("Loading curricula...")
            curr_count = seed_curricula(cur, entry_map)
            print(f"  -> {curr_count} curriculum records")

            print("Loading community data...")
            community_count = seed_community(cur)
            print(f"  -> {community_count} community records")
            print(f"     events: {_table_count(cur, 'community.events')}")
            print(f"     contributors: {_table_count(cur, 'community.contributors')}")
            print(f"     contributions: {_table_count(cur, 'community.contributions')}")

        conn.commit()

    total = tax_count + session_count + len(entry_map) + curr_count + community_count
    print(f"\nSeed complete: {total} total records processed.")


if __name__ == "__main__":
    main()

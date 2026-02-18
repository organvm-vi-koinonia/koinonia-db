#!/usr/bin/env python3
"""Master seeding script for ORGAN-VI koinonia Neon database.

Seeds all tables from koinonia-db/seed/ JSON files using UPSERT (ON CONFLICT DO UPDATE)
to ensure idempotent seeding — running twice produces the same PKs.

Usage:
    DATABASE_URL=postgresql://... python scripts/seed_all.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from koinonia_db.models.salon import (
    Participant,
    SalonSessionRow,
    Segment,
    TaxonomyNodeRow,
)
from koinonia_db.models.reading import (
    Curriculum,
    DiscussionQuestion,
    Entry,
    Guide,
    ReadingSessionRow,
    SessionEntry,
)
from koinonia_db.models.community import (
    Contributor,
    Contribution,
    Event,
)

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def get_engine():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, echo=False)


def seed_taxonomy(session: Session) -> dict[str, int]:
    """Seed taxonomy nodes with UPSERT on slug. Returns slug->id map."""
    data = json.loads((SEED_DIR / "taxonomy.json").read_text())
    slug_map: dict[str, int] = {}

    for root in data["nodes"]:
        stmt = pg_insert(TaxonomyNodeRow).values(
            slug=root["slug"],
            label=root["label"],
            organ_id=root.get("organ_id"),
            description=root["description"],
            parent_id=None,
        ).on_conflict_do_update(
            index_elements=["slug"],
            set_={"label": root["label"], "description": root["description"]},
        ).returning(TaxonomyNodeRow.id)
        root_id = session.execute(stmt).scalar_one()
        slug_map[root["slug"]] = root_id

        for child in root.get("children", []):
            stmt = pg_insert(TaxonomyNodeRow).values(
                slug=child["slug"],
                label=child["label"],
                organ_id=root.get("organ_id"),
                description=child["description"],
                parent_id=root_id,
            ).on_conflict_do_update(
                index_elements=["slug"],
                set_={"label": child["label"], "description": child["description"], "parent_id": root_id},
            ).returning(TaxonomyNodeRow.id)
            child_id = session.execute(stmt).scalar_one()
            slug_map[child["slug"]] = child_id

    session.commit()
    print(f"  Taxonomy: {len(slug_map)} nodes upserted.")
    return slug_map


def seed_salons(session: Session) -> list[int]:
    """Seed sample salon sessions. Uses title as natural key for upsert."""
    data = json.loads((SEED_DIR / "sample_sessions.json").read_text())
    ids: list[int] = []

    for s in data["sessions"]:
        dt = s["date"]
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00")).date()

        # Upsert session by title
        stmt = pg_insert(SalonSessionRow).values(
            title=s["title"],
            date=dt,
            format=s["format"],
            facilitator=s.get("facilitator"),
            notes=s.get("notes", ""),
            organ_tags=s.get("organ_tags", []),
        ).on_conflict_do_update(
            constraint=None,
            index_elements=None,
            set_={"notes": s.get("notes", ""), "organ_tags": s.get("organ_tags", [])},
        )
        # Sessions don't have a unique constraint on title, so use insert-or-fetch
        existing = session.execute(
            text("SELECT id FROM salons.sessions WHERE title = :t"),
            {"t": s["title"]},
        ).scalar_one_or_none()

        if existing:
            session.execute(
                text("UPDATE salons.sessions SET notes = :n, organ_tags = :ot WHERE id = :id"),
                {"n": s.get("notes", ""), "ot": s.get("organ_tags", []), "id": existing},
            )
            row_id = existing
        else:
            row = SalonSessionRow(
                title=s["title"], date=dt, format=s["format"],
                facilitator=s.get("facilitator"), notes=s.get("notes", ""),
                organ_tags=s.get("organ_tags", []),
            )
            session.add(row)
            session.flush()
            row_id = row.id

            for p in s.get("participants", []):
                session.add(Participant(
                    session_id=row_id,
                    name=p["name"],
                    role=p.get("role", "participant"),
                    consent_given=p.get("consent_given", False),
                ))
            for seg in s.get("segments", []):
                session.add(Segment(
                    session_id=row_id,
                    speaker=seg["speaker"],
                    text=seg["text"],
                    start_seconds=seg["start_seconds"],
                    end_seconds=seg["end_seconds"],
                    confidence=seg.get("confidence", 0.0),
                ))

        ids.append(row_id)

    session.commit()
    print(f"  Salons: {len(ids)} sessions upserted.")
    return ids


def seed_reading_entries(session: Session) -> dict[str, int]:
    """Seed reading entries with UPSERT on title+author composite."""
    data = json.loads((SEED_DIR / "reading_lists.json").read_text())
    key_map: dict[str, int] = {}

    for entry in data["entries"]:
        # Check for existing by title+author
        existing = session.execute(
            text("SELECT id FROM reading.entries WHERE title = :t AND author = :a"),
            {"t": entry["title"], "a": entry["author"]},
        ).scalar_one_or_none()

        if existing:
            session.execute(
                text("""UPDATE reading.entries
                        SET source_type = :st, url = :u, pages = :p, difficulty = :d, organ_tags = :ot
                        WHERE id = :id"""),
                {
                    "st": entry.get("source_type", "book"),
                    "u": entry.get("url"),
                    "p": entry.get("pages"),
                    "d": entry.get("difficulty", "intermediate"),
                    "ot": entry.get("organ_tags", []),
                    "id": existing,
                },
            )
            key_map[entry["key"]] = existing
        else:
            row = Entry(
                title=entry["title"],
                author=entry["author"],
                source_type=entry.get("source_type", "book"),
                url=entry.get("url"),
                pages=entry.get("pages"),
                difficulty=entry.get("difficulty", "intermediate"),
                organ_tags=entry.get("organ_tags", []),
            )
            session.add(row)
            session.flush()
            key_map[entry["key"]] = row.id

    session.commit()
    print(f"  Reading entries: {len(key_map)} entries upserted.")
    return key_map


def seed_curricula(session: Session, entry_map: dict[str, int]) -> list[int]:
    """Seed curricula with sessions, questions, guides, and entry links."""
    data = json.loads((SEED_DIR / "curricula.json").read_text())
    curriculum_ids: list[int] = []
    total_sessions = 0
    total_questions = 0
    total_guides = 0
    total_links = 0

    for c in data["curricula"]:
        # Check for existing by title
        existing = session.execute(
            text("SELECT id FROM reading.curricula WHERE title = :t"),
            {"t": c["title"]},
        ).scalar_one_or_none()

        if existing:
            curriculum_ids.append(existing)
            continue

        row = Curriculum(
            title=c["title"],
            theme=c["theme"],
            organ_focus=c.get("organ_focus"),
            duration_weeks=c["duration_weeks"],
            description=c["description"],
        )
        session.add(row)
        session.flush()
        curriculum_ids.append(row.id)

        for sess in c["sessions"]:
            srow = ReadingSessionRow(
                curriculum_id=row.id,
                week=sess["week"],
                title=sess["title"],
                duration_minutes=90,
            )
            session.add(srow)
            session.flush()
            total_sessions += 1

            for rkey in sess.get("readings", []):
                if rkey in entry_map:
                    session.add(SessionEntry(session_id=srow.id, entry_id=entry_map[rkey]))
                    total_links += 1

            for q in sess.get("questions", []):
                session.add(DiscussionQuestion(
                    session_id=srow.id, question_text=q, category="deep_dive",
                ))
                total_questions += 1

            questions = sess.get("questions", [])
            activities = sess.get("activities", [])
            session.add(Guide(
                session_id=srow.id,
                opening_questions=questions[:2],
                deep_dive_questions=questions[2:],
                activities=activities,
                closing_reflection=f"How has this session changed your understanding of {sess['title']}?",
            ))
            total_guides += 1

    session.commit()
    print(
        f"  Curricula: {len(curriculum_ids)} curricula, {total_sessions} sessions, "
        f"{total_questions} questions, {total_guides} guides, {total_links} entry links."
    )
    return curriculum_ids


def seed_community(session: Session) -> None:
    """Seed community events and contributors with UPSERT on github_handle."""
    # Upsert contributor
    existing_contrib = session.execute(
        text("SELECT id FROM community.contributors WHERE github_handle = :gh"),
        {"gh": "4444J99"},
    ).scalar_one_or_none()

    if existing_contrib:
        contrib_id = existing_contrib
    else:
        contrib = Contributor(
            github_handle="4444J99",
            name="4444J99",
            organs_active=["I", "II", "III", "IV", "V", "VI", "VII"],
            first_contribution_date=date(2026, 2, 9),
        )
        session.add(contrib)
        session.flush()
        contrib_id = contrib.id

    # Upsert contributions (by repo+type)
    contributions = [
        ("organvm-iv-taxis/orchestration-start-here", "code", "System architecture and orchestration"),
        ("organvm-v-logos/public-process", "essay", "10 meta-system essays (~40K words)"),
        ("organvm-vi-koinonia/community-hub", "code", "Community portal flagship"),
        ("organvm-vi-koinonia/salon-archive", "code", "Salon archive infrastructure"),
        ("organvm-vi-koinonia/reading-group-curriculum", "code", "Reading group curriculum system"),
    ]
    for repo, ctype, desc in contributions:
        existing = session.execute(
            text("SELECT id FROM community.contributions WHERE contributor_id = :cid AND repo = :r AND type = :t"),
            {"cid": contrib_id, "r": repo, "t": ctype},
        ).scalar_one_or_none()
        if not existing:
            session.add(Contribution(
                contributor_id=contrib_id, repo=repo, type=ctype,
                url=f"https://github.com/{repo}", date=date(2026, 2, 17),
                description=desc,
            ))

    # Upsert events (by title)
    events_data = [
        ("salon", "Recursive Systems as Creative Practice", date(2026, 2, 20),
         "Deep dive into self-referential structures as creative acts", "deep_dive", 8, "scheduled"),
        ("salon", "The AI-Conductor Model: Human Direction, Machine Volume", date(2026, 2, 27),
         "Socratic dialogue on the conductor metaphor for AI-assisted creation", "socratic_dialogue", 8, "scheduled"),
        ("reading_group", "Foundations of Recursive Systems — Week 1", date(2026, 3, 3),
         "Reading group launch: Strange Loops and Tangled Hierarchies", "discussion", 12, "planned"),
    ]
    for etype, title, edate, desc, fmt, cap, status in events_data:
        existing = session.execute(
            text("SELECT id FROM community.events WHERE title = :t"),
            {"t": title},
        ).scalar_one_or_none()
        if not existing:
            session.add(Event(
                type=etype, title=title, date=edate,
                description=desc, format=fmt, capacity=cap, status=status,
            ))

    session.commit()
    print("  Community: upserted contributor, contributions, and events.")


def main() -> None:
    print("ORGAN-VI Koinonia Database Seeder (UPSERT mode)")
    print("=" * 50)

    engine = get_engine()
    print(f"Connected to: {engine.url.host}")

    with Session(engine) as session:
        slug_map = seed_taxonomy(session)
        salon_ids = seed_salons(session)
        entry_map = seed_reading_entries(session)
        curriculum_ids = seed_curricula(session, entry_map)
        seed_community(session)

    print("=" * 50)
    print("Seeding complete (idempotent UPSERT)!")
    print(f"  Taxonomy nodes: {len(slug_map)}")
    print(f"  Salon sessions: {len(salon_ids)}")
    print(f"  Reading entries: {len(entry_map)}")
    print(f"  Curricula: {len(curriculum_ids)}")


if __name__ == "__main__":
    main()

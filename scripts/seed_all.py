#!/usr/bin/env python3
"""Master seeding script for ORGAN-VI koinonia Neon database.

Seeds all tables from koinonia-db/seed/ JSON files:
  - taxonomy nodes (40+ nodes across 8 organs)
  - salon sessions with participants and segments
  - reading entries (39 curated sources)
  - curricula with sessions, questions, guides, and entry linkages
  - community events and contributors

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
from sqlalchemy.orm import Session

# Add the package to path
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


def clear_tables(session: Session) -> None:
    """Delete existing seed data to allow re-seeding."""
    for table in [
        "community.contributions",
        "community.contributors",
        "community.events",
        "reading.guides",
        "reading.discussion_questions",
        "reading.session_entries",
        "reading.entries",
        "reading.sessions",
        "reading.curricula",
        "salons.segments",
        "salons.participants",
        "salons.sessions",
        "salons.taxonomy_nodes",
    ]:
        session.execute(text(f"DELETE FROM {table}"))
    session.commit()
    print("  Cleared existing data.")


def seed_taxonomy(session: Session) -> dict[str, int]:
    """Seed taxonomy nodes. Returns slug->id map."""
    data = json.loads((SEED_DIR / "taxonomy.json").read_text())
    slug_map: dict[str, int] = {}

    for root in data["nodes"]:
        node = TaxonomyNodeRow(
            slug=root["slug"],
            label=root["label"],
            organ_id=root.get("organ_id"),
            description=root["description"],
            parent_id=None,
        )
        session.add(node)
        session.flush()
        slug_map[root["slug"]] = node.id

        for child in root.get("children", []):
            child_node = TaxonomyNodeRow(
                slug=child["slug"],
                label=child["label"],
                organ_id=root.get("organ_id"),
                description=child["description"],
                parent_id=node.id,
            )
            session.add(child_node)
            session.flush()
            slug_map[child["slug"]] = child_node.id

    session.commit()
    print(f"  Taxonomy: {len(slug_map)} nodes seeded.")
    return slug_map


def seed_salons(session: Session) -> list[int]:
    """Seed sample salon sessions. Returns list of session IDs."""
    data = json.loads((SEED_DIR / "sample_sessions.json").read_text())
    ids: list[int] = []

    for s in data["sessions"]:
        row = SalonSessionRow(
            title=s["title"],
            date=datetime.fromisoformat(s["date"].replace("Z", "+00:00")).date()
            if isinstance(s["date"], str)
            else s["date"],
            format=s["format"],
            facilitator=s.get("facilitator"),
            notes=s.get("notes", ""),
            organ_tags=s.get("organ_tags", []),
        )
        session.add(row)
        session.flush()
        ids.append(row.id)

        for p in s.get("participants", []):
            session.add(
                Participant(
                    session_id=row.id,
                    name=p["name"],
                    role=p.get("role", "participant"),
                    consent_given=p.get("consent_given", False),
                )
            )

        for seg in s.get("segments", []):
            session.add(
                Segment(
                    session_id=row.id,
                    speaker=seg["speaker"],
                    text=seg["text"],
                    start_seconds=seg["start_seconds"],
                    end_seconds=seg["end_seconds"],
                    confidence=seg.get("confidence", 0.0),
                )
            )

    session.commit()
    print(f"  Salons: {len(ids)} sessions seeded ({sum(len(s.get('segments', [])) for s in data['sessions'])} segments, {sum(len(s.get('participants', [])) for s in data['sessions'])} participants).")
    return ids


def seed_reading_entries(session: Session) -> dict[str, int]:
    """Seed reading entries. Returns key->id map."""
    data = json.loads((SEED_DIR / "reading_lists.json").read_text())
    key_map: dict[str, int] = {}

    for entry in data["entries"]:
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
    print(f"  Reading entries: {len(key_map)} entries seeded.")
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

            # Link reading entries
            for rkey in sess.get("readings", []):
                if rkey in entry_map:
                    session.add(
                        SessionEntry(session_id=srow.id, entry_id=entry_map[rkey])
                    )
                    total_links += 1

            # Discussion questions
            for q in sess.get("questions", []):
                session.add(
                    DiscussionQuestion(
                        session_id=srow.id,
                        question_text=q,
                        category="deep_dive",
                    )
                )
                total_questions += 1

            # Discussion guide
            questions = sess.get("questions", [])
            activities = sess.get("activities", [])
            session.add(
                Guide(
                    session_id=srow.id,
                    opening_questions=questions[:2],
                    deep_dive_questions=questions[2:],
                    activities=activities,
                    closing_reflection=f"How has this session changed your understanding of {sess['title']}?",
                )
            )
            total_guides += 1

    session.commit()
    print(
        f"  Curricula: {len(curriculum_ids)} curricula, {total_sessions} sessions, "
        f"{total_questions} questions, {total_guides} guides, {total_links} entry links."
    )
    return curriculum_ids


def seed_community(session: Session) -> None:
    """Seed community events and contributors."""
    # Contributor: the system builder
    contrib = Contributor(
        github_handle="4444J99",
        name="4444J99",
        organs_active=["I", "II", "III", "IV", "V", "VI", "VII"],
        first_contribution_date=date(2026, 2, 9),
    )
    session.add(contrib)
    session.flush()

    # Key contributions
    contributions = [
        ("organvm-iv-taxis/orchestration-start-here", "code", "System architecture and orchestration"),
        ("organvm-v-logos/public-process", "essay", "10 meta-system essays (~40K words)"),
        ("organvm-vi-koinonia/community-hub", "code", "Community portal flagship"),
        ("organvm-vi-koinonia/salon-archive", "code", "Salon archive infrastructure"),
        ("organvm-vi-koinonia/reading-group-curriculum", "code", "Reading group curriculum system"),
    ]
    for repo, ctype, desc in contributions:
        session.add(
            Contribution(
                contributor_id=contrib.id,
                repo=repo,
                type=ctype,
                url=f"https://github.com/{repo}",
                date=date(2026, 2, 17),
                description=desc,
            )
        )

    # Community events
    events = [
        Event(
            type="salon",
            title="Recursive Systems as Creative Practice",
            date=date(2026, 2, 20),
            description="Deep dive into self-referential structures as creative acts",
            format="deep_dive",
            capacity=8,
            status="scheduled",
        ),
        Event(
            type="salon",
            title="The AI-Conductor Model: Human Direction, Machine Volume",
            date=date(2026, 2, 27),
            description="Socratic dialogue on the conductor metaphor for AI-assisted creation",
            format="socratic_dialogue",
            capacity=8,
            status="scheduled",
        ),
        Event(
            type="reading_group",
            title="Foundations of Recursive Systems — Week 1",
            date=date(2026, 3, 3),
            description="Reading group launch: Strange Loops and Tangled Hierarchies",
            format="discussion",
            capacity=12,
            status="planned",
        ),
    ]
    for e in events:
        session.add(e)

    session.commit()
    print(f"  Community: 1 contributor, {len(contributions)} contributions, {len(events)} events.")


def main() -> None:
    print("ORGAN-VI Koinonia Database Seeder")
    print("=" * 50)

    engine = get_engine()
    print(f"Connected to: {engine.url.host}")

    with Session(engine) as session:
        clear_tables(session)
        slug_map = seed_taxonomy(session)
        salon_ids = seed_salons(session)
        entry_map = seed_reading_entries(session)
        curriculum_ids = seed_curricula(session, entry_map)
        seed_community(session)

    print("=" * 50)
    print("Seeding complete!")
    print(f"  Taxonomy nodes: {len(slug_map)}")
    print(f"  Salon sessions: {len(salon_ids)}")
    print(f"  Reading entries: {len(entry_map)}")
    print(f"  Curricula: {len(curriculum_ids)}")


if __name__ == "__main__":
    main()

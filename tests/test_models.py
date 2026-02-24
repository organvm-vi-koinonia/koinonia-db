"""Tests for koinonia-db ORM models — verifies instantiation, attributes, and relationships."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import inspect

from koinonia_db.models.base import Base
from koinonia_db.models import (
    SalonSessionRow,
    Participant,
    Segment,
    TaxonomyNodeRow,
    Curriculum,
    ReadingSessionRow,
    Entry,
    SessionEntry,
    DiscussionQuestion,
    Guide,
    Event,
    Contributor,
    Contribution,
    LearnerProfileRow,
    LearningPathRow,
    LearningModuleRow,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_MODELS = [
    SalonSessionRow,
    Participant,
    Segment,
    TaxonomyNodeRow,
    Curriculum,
    ReadingSessionRow,
    Entry,
    SessionEntry,
    DiscussionQuestion,
    Guide,
    Event,
    Contributor,
    Contribution,
    LearnerProfileRow,
    LearningPathRow,
    LearningModuleRow,
]


def _column_names(model) -> set[str]:
    """Return the set of column names declared on a model's table."""
    return {c.name for c in model.__table__.columns}


def _relationship_names(model) -> set[str]:
    """Return the set of relationship names registered on a model's mapper."""
    mapper = inspect(model)
    return set(mapper.relationships.keys())


# ---------------------------------------------------------------------------
# Shared-Base verification
# ---------------------------------------------------------------------------


def test_all_models_share_same_base():
    """Every model class should inherit from the common Base."""
    for model in ALL_MODELS:
        assert issubclass(model, Base), f"{model.__name__} does not inherit from Base"


def test_base_metadata_includes_all_tables():
    """Base.metadata should contain tables contributed by every model module."""
    table_names = {t.name for t in Base.metadata.tables.values()}
    expected = {
        "sessions",            # salons + reading both have 'sessions'
        "participants",
        "segments",
        "taxonomy_nodes",
        "curricula",
        "entries",
        "session_entries",
        "discussion_questions",
        "guides",
        "events",
        "contributors",
        "contributions",
        "learner_profiles",
        "learning_paths",
        "learning_modules",
    }
    assert expected.issubset(table_names)


# ===========================================================================
# Salon models
# ===========================================================================


class TestSalonSessionRow:
    def test_tablename_and_schema(self):
        assert SalonSessionRow.__tablename__ == "sessions"
        assert SalonSessionRow.__table_args__["schema"] == "salons"

    def test_columns_present(self):
        cols = _column_names(SalonSessionRow)
        for name in ("id", "title", "date", "format", "facilitator",
                     "recording_url", "notes", "organ_tags", "created_at"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(SalonSessionRow)
        assert "participants" in rels
        assert "segments" in rels

    def test_instantiation(self):
        now = datetime.now(timezone.utc)
        session = SalonSessionRow(
            id=1,
            title="Test Salon",
            date=now,
            format="deep_dive",
            facilitator="Facilitator A",
            recording_url="https://example.com/rec",
            notes="Some notes",
        )
        assert session.id == 1
        assert session.title == "Test Salon"
        assert session.date == now
        assert session.format == "deep_dive"
        assert session.facilitator == "Facilitator A"
        assert session.recording_url == "https://example.com/rec"
        assert session.notes == "Some notes"


class TestParticipant:
    def test_tablename_and_schema(self):
        assert Participant.__tablename__ == "participants"
        assert Participant.__table_args__["schema"] == "salons"

    def test_columns_present(self):
        cols = _column_names(Participant)
        for name in ("id", "session_id", "name", "role", "consent_given"):
            assert name in cols, f"Missing column: {name}"

    def test_instantiation(self):
        p = Participant(id=10, session_id=1, name="Alice", role="facilitator", consent_given=True)
        assert p.id == 10
        assert p.session_id == 1
        assert p.name == "Alice"
        assert p.role == "facilitator"
        assert p.consent_given is True

    def test_relationship_to_session(self):
        rels = _relationship_names(Participant)
        assert "session" in rels


class TestSegment:
    def test_tablename_and_schema(self):
        assert Segment.__tablename__ == "segments"
        assert Segment.__table_args__["schema"] == "salons"

    def test_columns_present(self):
        cols = _column_names(Segment)
        for name in ("id", "session_id", "speaker", "text",
                     "start_seconds", "end_seconds", "confidence"):
            assert name in cols, f"Missing column: {name}"

    def test_instantiation(self):
        seg = Segment(
            id=5,
            session_id=1,
            speaker="Bob",
            text="Good evening.",
            start_seconds=0.0,
            end_seconds=3.5,
            confidence=0.95,
        )
        assert seg.id == 5
        assert seg.session_id == 1
        assert seg.speaker == "Bob"
        assert seg.text == "Good evening."
        assert seg.start_seconds == 0.0
        assert seg.end_seconds == 3.5
        assert seg.confidence == 0.95

    def test_relationship_to_session(self):
        rels = _relationship_names(Segment)
        assert "session" in rels


class TestTaxonomyNodeRow:
    def test_tablename_and_schema(self):
        assert TaxonomyNodeRow.__tablename__ == "taxonomy_nodes"
        assert TaxonomyNodeRow.__table_args__["schema"] == "salons"

    def test_columns_present(self):
        cols = _column_names(TaxonomyNodeRow)
        for name in ("id", "slug", "label", "parent_id", "description", "organ_id"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(TaxonomyNodeRow)
        assert "children" in rels
        assert "parent" in rels

    def test_instantiation(self):
        node = TaxonomyNodeRow(
            id=1,
            slug="vi-koinonia",
            label="Koinonia",
            parent_id=None,
            description="Community organ",
            organ_id=6,
        )
        assert node.id == 1
        assert node.slug == "vi-koinonia"
        assert node.label == "Koinonia"
        assert node.parent_id is None
        assert node.description == "Community organ"
        assert node.organ_id == 6


# ===========================================================================
# Reading models
# ===========================================================================


class TestCurriculum:
    def test_tablename_and_schema(self):
        assert Curriculum.__tablename__ == "curricula"
        assert Curriculum.__table_args__["schema"] == "reading"

    def test_columns_present(self):
        cols = _column_names(Curriculum)
        for name in ("id", "title", "theme", "organ_focus",
                     "duration_weeks", "description", "created_at"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(Curriculum)
        assert "sessions" in rels

    def test_instantiation(self):
        c = Curriculum(
            id=1,
            title="Recursive Systems",
            theme="theory",
            organ_focus="I",
            duration_weeks=6,
            description="A deep dive into recursion.",
        )
        assert c.id == 1
        assert c.title == "Recursive Systems"
        assert c.theme == "theory"
        assert c.organ_focus == "I"
        assert c.duration_weeks == 6
        assert c.description == "A deep dive into recursion."


class TestReadingSessionRow:
    def test_tablename_and_schema(self):
        assert ReadingSessionRow.__tablename__ == "sessions"
        assert ReadingSessionRow.__table_args__["schema"] == "reading"

    def test_columns_present(self):
        cols = _column_names(ReadingSessionRow)
        for name in ("id", "curriculum_id", "week", "title",
                     "duration_minutes", "completed", "date_scheduled"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(ReadingSessionRow)
        assert "curriculum" in rels
        assert "entries" in rels
        assert "discussion_questions" in rels
        assert "guide" in rels

    def test_instantiation(self):
        rs = ReadingSessionRow(
            id=1,
            curriculum_id=1,
            week=1,
            title="Week 1: Introduction",
            duration_minutes=90,
            completed=False,
            date_scheduled=date(2026, 3, 1),
        )
        assert rs.id == 1
        assert rs.curriculum_id == 1
        assert rs.week == 1
        assert rs.title == "Week 1: Introduction"
        assert rs.duration_minutes == 90
        assert rs.completed is False
        assert rs.date_scheduled == date(2026, 3, 1)


class TestEntry:
    def test_tablename_and_schema(self):
        assert Entry.__tablename__ == "entries"
        assert Entry.__table_args__["schema"] == "reading"

    def test_columns_present(self):
        cols = _column_names(Entry)
        for name in ("id", "title", "author", "source_type",
                     "url", "pages", "difficulty", "organ_tags"):
            assert name in cols, f"Missing column: {name}"

    def test_relationship_to_sessions(self):
        rels = _relationship_names(Entry)
        assert "sessions" in rels

    def test_instantiation(self):
        e = Entry(
            id=1,
            title="Godel, Escher, Bach",
            author="Douglas Hofstadter",
            source_type="book",
            url="https://example.com",
            pages="1-50",
            difficulty="advanced",
        )
        assert e.id == 1
        assert e.title == "Godel, Escher, Bach"
        assert e.author == "Douglas Hofstadter"
        assert e.source_type == "book"
        assert e.url == "https://example.com"
        assert e.pages == "1-50"
        assert e.difficulty == "advanced"


class TestSessionEntry:
    def test_tablename_and_schema(self):
        assert SessionEntry.__tablename__ == "session_entries"
        assert SessionEntry.__table_args__["schema"] == "reading"

    def test_columns_present(self):
        cols = _column_names(SessionEntry)
        assert "session_id" in cols
        assert "entry_id" in cols

    def test_instantiation(self):
        se = SessionEntry(session_id=1, entry_id=2)
        assert se.session_id == 1
        assert se.entry_id == 2


class TestDiscussionQuestion:
    def test_tablename_and_schema(self):
        assert DiscussionQuestion.__tablename__ == "discussion_questions"
        assert DiscussionQuestion.__table_args__["schema"] == "reading"

    def test_columns_present(self):
        cols = _column_names(DiscussionQuestion)
        for name in ("id", "session_id", "question_text", "category"):
            assert name in cols, f"Missing column: {name}"

    def test_relationship_to_session(self):
        rels = _relationship_names(DiscussionQuestion)
        assert "session" in rels

    def test_instantiation(self):
        dq = DiscussionQuestion(
            id=1,
            session_id=1,
            question_text="What is the main thesis?",
            category="deep_dive",
        )
        assert dq.id == 1
        assert dq.session_id == 1
        assert dq.question_text == "What is the main thesis?"
        assert dq.category == "deep_dive"


class TestGuide:
    def test_tablename_and_schema(self):
        assert Guide.__tablename__ == "guides"
        assert Guide.__table_args__["schema"] == "reading"

    def test_columns_present(self):
        cols = _column_names(Guide)
        for name in ("id", "session_id", "opening_questions",
                     "deep_dive_questions", "activities", "closing_reflection"):
            assert name in cols, f"Missing column: {name}"

    def test_relationship_to_session(self):
        rels = _relationship_names(Guide)
        assert "session" in rels

    def test_instantiation(self):
        g = Guide(
            id=1,
            session_id=1,
            closing_reflection="Reflect on what you learned.",
        )
        assert g.id == 1
        assert g.session_id == 1
        assert g.closing_reflection == "Reflect on what you learned."


# ===========================================================================
# Community models
# ===========================================================================


class TestEvent:
    def test_tablename_and_schema(self):
        assert Event.__tablename__ == "events"
        assert Event.__table_args__["schema"] == "community"

    def test_columns_present(self):
        cols = _column_names(Event)
        for name in ("id", "type", "title", "date", "description",
                     "format", "capacity", "registration_url", "status"):
            assert name in cols, f"Missing column: {name}"

    def test_instantiation(self):
        now = datetime.now(timezone.utc)
        ev = Event(
            id=1,
            type="salon",
            title="Community Salon #1",
            date=now,
            description="A community gathering.",
            format="virtual",
            capacity=50,
            registration_url="https://example.com/register",
            status="planned",
        )
        assert ev.id == 1
        assert ev.type == "salon"
        assert ev.title == "Community Salon #1"
        assert ev.date == now
        assert ev.description == "A community gathering."
        assert ev.format == "virtual"
        assert ev.capacity == 50
        assert ev.registration_url == "https://example.com/register"
        assert ev.status == "planned"


class TestContributor:
    def test_tablename_and_schema(self):
        assert Contributor.__tablename__ == "contributors"
        assert Contributor.__table_args__["schema"] == "community"

    def test_columns_present(self):
        cols = _column_names(Contributor)
        for name in ("id", "github_handle", "name",
                     "organs_active", "first_contribution_date"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(Contributor)
        assert "contributions" in rels

    def test_instantiation(self):
        c = Contributor(
            id=1,
            github_handle="alice-dev",
            name="Alice",
            first_contribution_date=date(2025, 1, 15),
        )
        assert c.id == 1
        assert c.github_handle == "alice-dev"
        assert c.name == "Alice"
        assert c.first_contribution_date == date(2025, 1, 15)


class TestContribution:
    def test_tablename_and_schema(self):
        assert Contribution.__tablename__ == "contributions"
        assert Contribution.__table_args__["schema"] == "community"

    def test_columns_present(self):
        cols = _column_names(Contribution)
        for name in ("id", "contributor_id", "repo", "type",
                     "url", "date", "description"):
            assert name in cols, f"Missing column: {name}"

    def test_relationship_to_contributor(self):
        rels = _relationship_names(Contribution)
        assert "contributor" in rels

    def test_instantiation(self):
        c = Contribution(
            id=1,
            contributor_id=1,
            repo="koinonia-db",
            type="pull_request",
            url="https://github.com/org/repo/pull/1",
            date=date(2025, 6, 1),
            description="Added tests",
        )
        assert c.id == 1
        assert c.contributor_id == 1
        assert c.repo == "koinonia-db"
        assert c.type == "pull_request"
        assert c.url == "https://github.com/org/repo/pull/1"
        assert c.date == date(2025, 6, 1)
        assert c.description == "Added tests"


# ===========================================================================
# Syllabus models
# ===========================================================================


class TestLearnerProfileRow:
    def test_tablename_and_schema(self):
        assert LearnerProfileRow.__tablename__ == "learner_profiles"
        assert LearnerProfileRow.__table_args__["schema"] == "syllabus"

    def test_columns_present(self):
        cols = _column_names(LearnerProfileRow)
        for name in ("id", "name", "organs_of_interest",
                     "level", "completed_modules", "created_at"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(LearnerProfileRow)
        assert "paths" in rels

    def test_instantiation(self):
        lp = LearnerProfileRow(
            id=1,
            name="Learner One",
            level="beginner",
        )
        assert lp.id == 1
        assert lp.name == "Learner One"
        assert lp.level == "beginner"


class TestLearningPathRow:
    def test_tablename_and_schema(self):
        assert LearningPathRow.__tablename__ == "learning_paths"
        assert LearningPathRow.__table_args__["schema"] == "syllabus"

    def test_columns_present(self):
        cols = _column_names(LearningPathRow)
        for name in ("id", "path_id", "title", "learner_id",
                     "total_hours", "created_at"):
            assert name in cols, f"Missing column: {name}"

    def test_relationships_declared(self):
        rels = _relationship_names(LearningPathRow)
        assert "learner" in rels
        assert "modules" in rels

    def test_instantiation(self):
        lp = LearningPathRow(
            id=1,
            path_id="abc123def456",
            title="Intro to Theoria",
            learner_id=1,
            total_hours=10.0,
        )
        assert lp.id == 1
        assert lp.path_id == "abc123def456"
        assert lp.title == "Intro to Theoria"
        assert lp.learner_id == 1
        assert lp.total_hours == 10.0


class TestLearningModuleRow:
    def test_tablename_and_schema(self):
        assert LearningModuleRow.__tablename__ == "learning_modules"
        assert LearningModuleRow.__table_args__["schema"] == "syllabus"

    def test_columns_present(self):
        cols = _column_names(LearningModuleRow)
        for name in ("id", "path_id", "module_id", "title", "organ",
                     "difficulty", "readings", "questions",
                     "estimated_hours", "seq"):
            assert name in cols, f"Missing column: {name}"

    def test_relationship_to_path(self):
        rels = _relationship_names(LearningModuleRow)
        assert "path" in rels

    def test_instantiation(self):
        lm = LearningModuleRow(
            id=1,
            path_id=1,
            module_id="mod-001",
            title="Foundations of Recursion",
            organ="I",
            difficulty="beginner",
            estimated_hours=2.5,
            seq=1,
        )
        assert lm.id == 1
        assert lm.path_id == 1
        assert lm.module_id == "mod-001"
        assert lm.title == "Foundations of Recursion"
        assert lm.organ == "I"
        assert lm.difficulty == "beginner"
        assert lm.estimated_hours == 2.5
        assert lm.seq == 1


# ===========================================================================
# Cross-cutting checks
# ===========================================================================


def test_all_models_importable_from_top_level():
    """Every model listed in __all__ should be importable from koinonia_db.models."""
    from koinonia_db import models
    for name in models.__all__:
        assert hasattr(models, name), f"{name} not accessible on koinonia_db.models"


def test_syllabus_service_importable():
    """generate_learning_path should be importable from koinonia_db."""
    from koinonia_db.syllabus_service import generate_learning_path
    assert callable(generate_learning_path)


def test_syllabus_service_reexported():
    """generate_learning_path should be importable from koinonia_db top-level."""
    from koinonia_db import generate_learning_path
    assert callable(generate_learning_path)

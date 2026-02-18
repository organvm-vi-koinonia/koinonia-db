"""Tests for koinonia-db models — verifies ORM mappings work correctly."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session

from koinonia_db.models import (
    Base,
    SalonSessionRow,
    Participant,
    Segment,
    TaxonomyNodeRow,
    Curriculum,
    ReadingSessionRow,
    Entry,
    DiscussionQuestion,
    Guide,
    Event,
    Contributor,
    Contribution,
)
from koinonia_db.models.syllabus import LearnerProfileRow, LearningPathRow, LearningModuleRow


def test_models_importable():
    """All model classes should be importable."""
    assert SalonSessionRow is not None
    assert Participant is not None
    assert Segment is not None
    assert TaxonomyNodeRow is not None
    assert Curriculum is not None
    assert ReadingSessionRow is not None
    assert Entry is not None
    assert DiscussionQuestion is not None
    assert Guide is not None
    assert Event is not None
    assert Contributor is not None
    assert Contribution is not None


def test_base_metadata_has_tables():
    """Base.metadata should include tables from all schemas."""
    table_names = {t.name for t in Base.metadata.tables.values()}
    assert "sessions" in table_names  # from salons
    assert "curricula" in table_names  # from reading
    assert "events" in table_names  # from community
    assert "taxonomy_nodes" in table_names
    assert "participants" in table_names
    assert "segments" in table_names
    assert "entries" in table_names
    assert "contributors" in table_names
    assert "contributions" in table_names
    assert "learner_profiles" in table_names  # from syllabus
    assert "learning_paths" in table_names
    assert "learning_modules" in table_names


# ── Syllabus model structure tests (no DB required) ────────────


def test_syllabus_models_importable():
    """Syllabus model classes should be importable with correct table config."""
    assert LearnerProfileRow.__tablename__ == "learner_profiles"
    assert LearningPathRow.__tablename__ == "learning_paths"
    assert LearningModuleRow.__tablename__ == "learning_modules"


def test_syllabus_models_have_schemas():
    """All syllabus models use the syllabus schema."""
    assert LearnerProfileRow.__table_args__["schema"] == "syllabus"
    assert LearningPathRow.__table_args__["schema"] == "syllabus"
    assert LearningModuleRow.__table_args__["schema"] == "syllabus"


def test_learner_profile_columns():
    """LearnerProfileRow has expected columns."""
    cols = {c.name for c in LearnerProfileRow.__table__.columns}
    assert "id" in cols
    assert "name" in cols
    assert "organs_of_interest" in cols
    assert "level" in cols
    assert "completed_modules" in cols


def test_learning_path_columns():
    """LearningPathRow has expected columns."""
    cols = {c.name for c in LearningPathRow.__table__.columns}
    assert "id" in cols
    assert "path_id" in cols
    assert "title" in cols
    assert "learner_id" in cols
    assert "total_hours" in cols


def test_learning_module_columns():
    """LearningModuleRow has expected columns."""
    cols = {c.name for c in LearningModuleRow.__table__.columns}
    assert "id" in cols
    assert "path_id" in cols
    assert "module_id" in cols
    assert "title" in cols
    assert "organ" in cols
    assert "difficulty" in cols
    assert "readings" in cols
    assert "questions" in cols
    assert "estimated_hours" in cols
    assert "seq" in cols


def test_learning_path_has_learner_relationship():
    """LearningPathRow has a relationship to LearnerProfileRow."""
    from sqlalchemy.orm import RelationshipProperty
    mapper = inspect(LearningPathRow)
    assert "learner" in mapper.relationships
    assert "modules" in mapper.relationships


# ── Syllabus service structure tests ─────────────────────────────


def test_syllabus_service_importable():
    """generate_learning_path should be importable from koinonia_db."""
    from koinonia_db.syllabus_service import generate_learning_path
    assert callable(generate_learning_path)


def test_syllabus_service_has_organ_map():
    """Service should export ORGAN_MAP with all 8 organs."""
    from koinonia_db.syllabus_service import ORGAN_MAP
    assert len(ORGAN_MAP) == 8
    assert ORGAN_MAP["I"] == "i-theoria"
    assert ORGAN_MAP["VIII"] == "viii-meta"


def test_syllabus_service_reexported():
    """generate_learning_path should be importable from koinonia_db top-level."""
    from koinonia_db import generate_learning_path
    assert callable(generate_learning_path)

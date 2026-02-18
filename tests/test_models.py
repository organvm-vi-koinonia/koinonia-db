"""Tests for koinonia-db models — verifies ORM mappings work correctly."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
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


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with all schemas."""
    eng = create_engine("sqlite:///:memory:")
    with eng.connect() as conn:
        # SQLite doesn't support schemas natively — create tables without schema
        conn.execute(text("ATTACH DATABASE ':memory:' AS salons"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS reading"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS community"))
        conn.commit()
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


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

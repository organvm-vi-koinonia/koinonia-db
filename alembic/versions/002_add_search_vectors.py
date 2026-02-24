"""Add tsvector search_vector columns and GIN indexes for full-text search.

Revision ID: 002
Revises: 001
Create Date: 2026-02-23

Tables affected:
  - salons.sessions (title + notes)
  - salons.segments (text)
  - salons.taxonomy_nodes (label + description)
  - reading.entries (title + author)
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- salons.sessions ---
    op.execute("""
        ALTER TABLE salons.sessions
        ADD COLUMN IF NOT EXISTS search_vector tsvector
    """)
    op.execute("""
        UPDATE salons.sessions SET search_vector =
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(notes, ''))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_search_vector
        ON salons.sessions USING GIN (search_vector)
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION salons.sessions_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.notes, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_sessions_search_vector ON salons.sessions
    """)
    op.execute("""
        CREATE TRIGGER trg_sessions_search_vector
        BEFORE INSERT OR UPDATE ON salons.sessions
        FOR EACH ROW EXECUTE FUNCTION salons.sessions_search_vector_update()
    """)

    # --- salons.segments ---
    op.execute("""
        ALTER TABLE salons.segments
        ADD COLUMN IF NOT EXISTS search_vector tsvector
    """)
    op.execute("""
        UPDATE salons.segments SET search_vector =
            to_tsvector('english', coalesce(text, ''))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_segments_search_vector
        ON salons.segments USING GIN (search_vector)
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION salons.segments_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('english', coalesce(NEW.text, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_segments_search_vector ON salons.segments
    """)
    op.execute("""
        CREATE TRIGGER trg_segments_search_vector
        BEFORE INSERT OR UPDATE ON salons.segments
        FOR EACH ROW EXECUTE FUNCTION salons.segments_search_vector_update()
    """)

    # --- salons.taxonomy_nodes ---
    op.execute("""
        ALTER TABLE salons.taxonomy_nodes
        ADD COLUMN IF NOT EXISTS search_vector tsvector
    """)
    op.execute("""
        UPDATE salons.taxonomy_nodes SET search_vector =
            to_tsvector('english', coalesce(label, '') || ' ' || coalesce(description, ''))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_taxonomy_nodes_search_vector
        ON salons.taxonomy_nodes USING GIN (search_vector)
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION salons.taxonomy_nodes_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('english', coalesce(NEW.label, '') || ' ' || coalesce(NEW.description, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_taxonomy_nodes_search_vector ON salons.taxonomy_nodes
    """)
    op.execute("""
        CREATE TRIGGER trg_taxonomy_nodes_search_vector
        BEFORE INSERT OR UPDATE ON salons.taxonomy_nodes
        FOR EACH ROW EXECUTE FUNCTION salons.taxonomy_nodes_search_vector_update()
    """)

    # --- reading.entries ---
    op.execute("""
        ALTER TABLE reading.entries
        ADD COLUMN IF NOT EXISTS search_vector tsvector
    """)
    op.execute("""
        UPDATE reading.entries SET search_vector =
            to_tsvector('english', coalesce(title, '') || ' by ' || coalesce(author, ''))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_entries_search_vector
        ON reading.entries USING GIN (search_vector)
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION reading.entries_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('english', coalesce(NEW.title, '') || ' by ' || coalesce(NEW.author, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_entries_search_vector ON reading.entries
    """)
    op.execute("""
        CREATE TRIGGER trg_entries_search_vector
        BEFORE INSERT OR UPDATE ON reading.entries
        FOR EACH ROW EXECUTE FUNCTION reading.entries_search_vector_update()
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_entries_search_vector ON reading.entries")
    op.execute("DROP FUNCTION IF EXISTS reading.entries_search_vector_update()")
    op.execute("DROP TRIGGER IF EXISTS trg_taxonomy_nodes_search_vector ON salons.taxonomy_nodes")
    op.execute("DROP FUNCTION IF EXISTS salons.taxonomy_nodes_search_vector_update()")
    op.execute("DROP TRIGGER IF EXISTS trg_segments_search_vector ON salons.segments")
    op.execute("DROP FUNCTION IF EXISTS salons.segments_search_vector_update()")
    op.execute("DROP TRIGGER IF EXISTS trg_sessions_search_vector ON salons.sessions")
    op.execute("DROP FUNCTION IF EXISTS salons.sessions_search_vector_update()")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS reading.idx_entries_search_vector")
    op.execute("DROP INDEX IF EXISTS salons.idx_taxonomy_nodes_search_vector")
    op.execute("DROP INDEX IF EXISTS salons.idx_segments_search_vector")
    op.execute("DROP INDEX IF EXISTS salons.idx_sessions_search_vector")

    # Drop columns
    op.drop_column("entries", "search_vector", schema="reading")
    op.drop_column("taxonomy_nodes", "search_vector", schema="salons")
    op.drop_column("segments", "search_vector", schema="salons")
    op.drop_column("sessions", "search_vector", schema="salons")

"""Add tsvector columns and GIN indexes for full-text search.

Revision ID: 002
Revises: 001
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # salons.sessions — search title (A) + notes (B)
    op.execute("""
        ALTER TABLE salons.sessions
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(notes, '')), 'B')
        ) STORED
    """)
    op.execute("""
        CREATE INDEX idx_sessions_search ON salons.sessions USING GIN (search_vector)
    """)

    # salons.segments — search text
    op.execute("""
        ALTER TABLE salons.segments
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(text, ''))
        ) STORED
    """)
    op.execute("""
        CREATE INDEX idx_segments_search ON salons.segments USING GIN (search_vector)
    """)

    # reading.entries — search title (A) + author (B)
    op.execute("""
        ALTER TABLE reading.entries
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(author, '')), 'B')
        ) STORED
    """)
    op.execute("""
        CREATE INDEX idx_entries_search ON reading.entries USING GIN (search_vector)
    """)

    # salons.taxonomy_nodes — search label (A) + description (B)
    op.execute("""
        ALTER TABLE salons.taxonomy_nodes
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(label, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
        ) STORED
    """)
    op.execute("""
        CREATE INDEX idx_taxonomy_search ON salons.taxonomy_nodes USING GIN (search_vector)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS salons.idx_taxonomy_search")
    op.execute("ALTER TABLE salons.taxonomy_nodes DROP COLUMN IF EXISTS search_vector")
    op.execute("DROP INDEX IF EXISTS reading.idx_entries_search")
    op.execute("ALTER TABLE reading.entries DROP COLUMN IF EXISTS search_vector")
    op.execute("DROP INDEX IF EXISTS salons.idx_segments_search")
    op.execute("ALTER TABLE salons.segments DROP COLUMN IF EXISTS search_vector")
    op.execute("DROP INDEX IF EXISTS salons.idx_sessions_search")
    op.execute("ALTER TABLE salons.sessions DROP COLUMN IF EXISTS search_vector")

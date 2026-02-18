"""Initial schema: salons, reading, community.

Revision ID: 001
Revises: None
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS salons")
    op.execute("CREATE SCHEMA IF NOT EXISTS reading")
    op.execute("CREATE SCHEMA IF NOT EXISTS community")

    # --- Salons ---
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("format", sa.String(50), server_default="deep_dive"),
        sa.Column("facilitator", sa.Text),
        sa.Column("recording_url", sa.Text),
        sa.Column("notes", sa.Text, server_default=""),
        sa.Column("organ_tags", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="salons",
    )
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("salons.sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("role", sa.String(50), server_default="participant"),
        sa.Column("consent_given", sa.Boolean, server_default="false"),
        schema="salons",
    )
    op.create_table(
        "segments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("salons.sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("speaker", sa.Text, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("start_seconds", sa.Float, nullable=False),
        sa.Column("end_seconds", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, server_default="0.0"),
        schema="salons",
    )
    op.create_table(
        "taxonomy_nodes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("salons.taxonomy_nodes.id")),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("organ_id", sa.Integer),
        schema="salons",
    )

    # --- Reading ---
    op.create_table(
        "curricula",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("theme", sa.String(100), server_default="general"),
        sa.Column("organ_focus", sa.String(50)),
        sa.Column("duration_weeks", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="reading",
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("curriculum_id", sa.Integer, sa.ForeignKey("reading.curricula.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("duration_minutes", sa.Integer, server_default="90"),
        sa.Column("completed", sa.Boolean, server_default="false"),
        sa.Column("date_scheduled", sa.Date),
        schema="reading",
    )
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("author", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(50), server_default="book"),
        sa.Column("url", sa.Text),
        sa.Column("pages", sa.String(100)),
        sa.Column("difficulty", sa.String(20), server_default="intermediate"),
        sa.Column("organ_tags", sa.ARRAY(sa.String), server_default="{}"),
        schema="reading",
    )
    op.create_table(
        "session_entries",
        sa.Column("session_id", sa.Integer, sa.ForeignKey("reading.sessions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("entry_id", sa.Integer, sa.ForeignKey("reading.entries.id", ondelete="CASCADE"), primary_key=True),
        schema="reading",
    )
    op.create_table(
        "discussion_questions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("reading.sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), server_default="deep_dive"),
        schema="reading",
    )
    op.create_table(
        "guides",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("reading.sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opening_questions", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("deep_dive_questions", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("activities", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("closing_reflection", sa.Text, server_default=""),
        schema="reading",
    )

    # --- Community ---
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("format", sa.String(50), server_default="virtual"),
        sa.Column("capacity", sa.Integer),
        sa.Column("registration_url", sa.Text),
        sa.Column("status", sa.String(30), server_default="planned"),
        schema="community",
    )
    op.create_table(
        "contributors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("github_handle", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("organs_active", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("first_contribution_date", sa.Date, server_default=sa.func.current_date()),
        schema="community",
    )
    op.create_table(
        "contributions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("contributor_id", sa.Integer, sa.ForeignKey("community.contributors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repo", sa.String(200), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("url", sa.Text),
        sa.Column("date", sa.Date, server_default=sa.func.current_date()),
        sa.Column("description", sa.Text, server_default=""),
        schema="community",
    )


def downgrade() -> None:
    op.drop_table("contributions", schema="community")
    op.drop_table("contributors", schema="community")
    op.drop_table("events", schema="community")
    op.drop_table("guides", schema="reading")
    op.drop_table("discussion_questions", schema="reading")
    op.drop_table("session_entries", schema="reading")
    op.drop_table("entries", schema="reading")
    op.drop_table("sessions", schema="reading")
    op.drop_table("curricula", schema="reading")
    op.drop_table("taxonomy_nodes", schema="salons")
    op.drop_table("segments", schema="salons")
    op.drop_table("participants", schema="salons")
    op.drop_table("sessions", schema="salons")
    op.execute("DROP SCHEMA IF EXISTS community")
    op.execute("DROP SCHEMA IF EXISTS reading")
    op.execute("DROP SCHEMA IF EXISTS salons")

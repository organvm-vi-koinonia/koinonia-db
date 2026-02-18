"""Create syllabus schema and tables for adaptive learning paths.

Revision ID: 003
Revises: 002
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS syllabus")

    op.create_table(
        "learner_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("organs_of_interest", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("level", sa.String(20), server_default="beginner"),
        sa.Column("completed_modules", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="syllabus",
    )

    op.create_table(
        "learning_paths",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("path_id", sa.String(32), unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("learner_id", sa.Integer, sa.ForeignKey("syllabus.learner_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_hours", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="syllabus",
    )

    op.create_table(
        "learning_modules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("path_id", sa.Integer, sa.ForeignKey("syllabus.learning_paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(100), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("organ", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(20), server_default="beginner"),
        sa.Column("readings", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("questions", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("estimated_hours", sa.Float, server_default="2.0"),
        sa.Column("seq", sa.Integer, server_default="0"),
        schema="syllabus",
    )


def downgrade() -> None:
    op.drop_table("learning_modules", schema="syllabus")
    op.drop_table("learning_paths", schema="syllabus")
    op.drop_table("learner_profiles", schema="syllabus")
    op.execute("DROP SCHEMA IF EXISTS syllabus")

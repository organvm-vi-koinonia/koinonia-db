"""Reading group models: curricula, sessions, entries, guides."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from koinonia_db.models.base import Base, TimestampMixin


class Curriculum(TimestampMixin, Base):
    __tablename__ = "curricula"
    __table_args__ = {"schema": "reading"}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str] = mapped_column(String(100), default="general")
    organ_focus: Mapped[Optional[str]] = mapped_column(String(50))
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    sessions: Mapped[list[ReadingSessionRow]] = relationship(
        back_populates="curriculum", cascade="all, delete-orphan"
    )


class ReadingSessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "reading"}

    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(
        ForeignKey("reading.curricula.id", ondelete="CASCADE")
    )
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    completed: Mapped[bool] = mapped_column(default=False)
    date_scheduled: Mapped[Optional[date]] = mapped_column()

    curriculum: Mapped[Curriculum] = relationship(back_populates="sessions")
    entries: Mapped[list[Entry]] = relationship(
        secondary="reading.session_entries", back_populates="sessions"
    )
    discussion_questions: Mapped[list[DiscussionQuestion]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    guide: Mapped[Optional[Guide]] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )


class Entry(Base):
    __tablename__ = "entries"
    __table_args__ = {"schema": "reading"}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="book")
    url: Mapped[Optional[str]] = mapped_column(Text)
    pages: Mapped[Optional[str]] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(20), default="intermediate")
    organ_tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])

    sessions: Mapped[list[ReadingSessionRow]] = relationship(
        secondary="reading.session_entries", back_populates="entries"
    )


class SessionEntry(Base):
    __tablename__ = "session_entries"
    __table_args__ = {"schema": "reading"}

    session_id: Mapped[int] = mapped_column(
        ForeignKey("reading.sessions.id", ondelete="CASCADE"), primary_key=True
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("reading.entries.id", ondelete="CASCADE"), primary_key=True
    )


class DiscussionQuestion(Base):
    __tablename__ = "discussion_questions"
    __table_args__ = {"schema": "reading"}

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("reading.sessions.id", ondelete="CASCADE")
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="deep_dive")

    session: Mapped[ReadingSessionRow] = relationship(back_populates="discussion_questions")


class Guide(Base):
    __tablename__ = "guides"
    __table_args__ = {"schema": "reading"}

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("reading.sessions.id", ondelete="CASCADE")
    )
    opening_questions: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    deep_dive_questions: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    activities: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    closing_reflection: Mapped[str] = mapped_column(Text, default="")

    session: Mapped[ReadingSessionRow] = relationship(back_populates="guide")

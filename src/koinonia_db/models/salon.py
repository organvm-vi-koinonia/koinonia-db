"""Salon archive models: sessions, participants, segments, taxonomy."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, ARRAY, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from koinonia_db.models.base import Base, TimestampMixin


class SalonSessionRow(TimestampMixin, Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "salons"}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[datetime] = mapped_column(nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="deep_dive")
    facilitator: Mapped[Optional[str]] = mapped_column(Text)
    recording_url: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    organ_tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])

    participants: Mapped[list[Participant]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    segments: Mapped[list[Segment]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = {"schema": "salons"}

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("salons.sessions.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="participant")
    consent_given: Mapped[bool] = mapped_column(default=False)

    session: Mapped[SalonSessionRow] = relationship(back_populates="participants")


class Segment(Base):
    __tablename__ = "segments"
    __table_args__ = {"schema": "salons"}

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("salons.sessions.id", ondelete="CASCADE"))
    speaker: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    session: Mapped[SalonSessionRow] = relationship(back_populates="segments")


class TaxonomyNodeRow(Base):
    __tablename__ = "taxonomy_nodes"
    __table_args__ = {"schema": "salons"}

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("salons.taxonomy_nodes.id")
    )
    description: Mapped[str] = mapped_column(Text, default="")
    organ_id: Mapped[Optional[int]] = mapped_column()

    children: Mapped[list[TaxonomyNodeRow]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent: Mapped[Optional[TaxonomyNodeRow]] = relationship(
        back_populates="children",
        remote_side="TaxonomyNodeRow.id",
    )

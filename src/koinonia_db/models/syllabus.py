"""Syllabus models: learner profiles, learning paths, learning modules."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, ARRAY, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from koinonia_db.models.base import Base, TimestampMixin


class LearnerProfileRow(TimestampMixin, Base):
    __tablename__ = "learner_profiles"
    __table_args__ = {"schema": "syllabus"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organs_of_interest: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    level: Mapped[str] = mapped_column(String(20), default="beginner")
    completed_modules: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])

    paths: Mapped[list[LearningPathRow]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )


class LearningPathRow(TimestampMixin, Base):
    __tablename__ = "learning_paths"
    __table_args__ = {"schema": "syllabus"}

    id: Mapped[int] = mapped_column(primary_key=True)
    path_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    learner_id: Mapped[int] = mapped_column(
        ForeignKey("syllabus.learner_profiles.id", ondelete="CASCADE")
    )
    total_hours: Mapped[float] = mapped_column(Float, default=0.0)

    learner: Mapped[LearnerProfileRow] = relationship(back_populates="paths")
    modules: Mapped[list[LearningModuleRow]] = relationship(
        back_populates="path", cascade="all, delete-orphan"
    )


class LearningModuleRow(Base):
    __tablename__ = "learning_modules"
    __table_args__ = {"schema": "syllabus"}

    id: Mapped[int] = mapped_column(primary_key=True)
    path_id: Mapped[int] = mapped_column(
        ForeignKey("syllabus.learning_paths.id", ondelete="CASCADE")
    )
    module_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    organ: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    readings: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    questions: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    estimated_hours: Mapped[float] = mapped_column(Float, default=2.0)
    seq: Mapped[int] = mapped_column(Integer, default=0)

    path: Mapped[LearningPathRow] = relationship(back_populates="modules")

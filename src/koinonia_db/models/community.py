"""Community hub models: events, contributors, contributions."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from koinonia_db.models.base import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "community"}

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[datetime] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    format: Mapped[str] = mapped_column(String(50), default="virtual")
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    registration_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="planned")


class Contributor(Base):
    __tablename__ = "contributors"
    __table_args__ = {"schema": "community"}

    id: Mapped[int] = mapped_column(primary_key=True)
    github_handle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organs_active: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=[])
    first_contribution_date: Mapped[date] = mapped_column(default=date.today)

    contributions: Mapped[list[Contribution]] = relationship(
        back_populates="contributor", cascade="all, delete-orphan"
    )


class Contribution(Base):
    __tablename__ = "contributions"
    __table_args__ = {"schema": "community"}

    id: Mapped[int] = mapped_column(primary_key=True)
    contributor_id: Mapped[int] = mapped_column(
        ForeignKey("community.contributors.id", ondelete="CASCADE")
    )
    repo: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text)
    date: Mapped[date] = mapped_column(default=date.today)
    description: Mapped[str] = mapped_column(Text, default="")

    contributor: Mapped[Contributor] = relationship(back_populates="contributions")

"""Shared database configuration utilities for ORGAN-VI repos."""

from __future__ import annotations

import os


def require_database_url() -> str:
    """Read DATABASE_URL from environment and convert to psycopg driver format.

    Raises RuntimeError if DATABASE_URL is not set.
    All ORGAN-VI repos should use this instead of reimplementing
    the postgresql:// -> postgresql+psycopg:// conversion.
    """
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

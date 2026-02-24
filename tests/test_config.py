"""Tests for koinonia_db.config — DATABASE_URL resolution and driver conversion."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from koinonia_db.config import require_database_url


class TestRequireDatabaseUrl:
    def test_raises_when_env_var_not_set(self):
        """require_database_url() should raise RuntimeError when DATABASE_URL is absent."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("DATABASE_URL", None)
            with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
                require_database_url()

    def test_raises_when_env_var_empty_string(self):
        """require_database_url() should raise RuntimeError for empty DATABASE_URL."""
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
                require_database_url()

    def test_converts_postgresql_to_psycopg(self):
        """postgresql:// should be rewritten to postgresql+psycopg://."""
        url = "postgresql://user:secret@db.example.com:5432/koinonia"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = require_database_url()
        assert result == "postgresql+psycopg://user:secret@db.example.com:5432/koinonia"

    def test_passes_through_psycopg_url_unchanged(self):
        """A URL already containing +psycopg should not be modified."""
        url = "postgresql+psycopg://user:secret@db.example.com:5432/koinonia"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = require_database_url()
        assert result == url

    def test_passes_through_other_schemes_unchanged(self):
        """Non-postgresql schemes (sqlite, mysql, etc.) should pass through as-is."""
        sqlite_url = "sqlite:///tmp/test.db"
        with patch.dict(os.environ, {"DATABASE_URL": sqlite_url}):
            result = require_database_url()
        assert result == sqlite_url

    def test_converts_only_first_occurrence(self):
        """Only the scheme prefix should be replaced, not embedded occurrences."""
        url = "postgresql://user@host/postgresql_db"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = require_database_url()
        # Only the leading "postgresql://" is converted
        assert result == "postgresql+psycopg://user@host/postgresql_db"
        # The "postgresql" in the database name is untouched
        assert result.endswith("/postgresql_db")

    def test_neon_style_url_converted(self):
        """Neon-format URLs with query params should be handled correctly."""
        url = "postgresql://user:pass@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = require_database_url()
        assert result.startswith("postgresql+psycopg://")
        assert "sslmode=require" in result

    def test_does_not_double_convert_psycopg2(self):
        """A URL using postgresql+psycopg2:// should not be modified (contains +psycopg)."""
        url = "postgresql+psycopg2://user:pass@host/db"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = require_database_url()
        assert result == url

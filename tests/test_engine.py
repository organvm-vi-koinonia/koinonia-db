"""Tests for koinonia_db.engine — async engine factory and session management."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import koinonia_db.engine as engine_module
from koinonia_db.engine import (
    get_database_url,
    get_engine,
    get_session_factory,
    dispose_engine,
)


@pytest.fixture(autouse=True)
def _reset_engine_singleton():
    """Ensure the module-level _engine is None before and after each test."""
    engine_module._engine = None
    yield
    engine_module._engine = None


# ---------------------------------------------------------------------------
# get_database_url()
# ---------------------------------------------------------------------------


class TestGetDatabaseUrl:
    def test_raises_when_env_var_missing(self):
        """get_database_url() should raise RuntimeError when DATABASE_URL is unset."""
        with patch.dict(os.environ, {}, clear=True):
            # Also clear DATABASE_URL specifically in case it exists
            os.environ.pop("DATABASE_URL", None)
            with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
                get_database_url()

    def test_raises_when_env_var_empty(self):
        """get_database_url() should raise RuntimeError when DATABASE_URL is empty string."""
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
                get_database_url()

    def test_converts_postgresql_to_psycopg(self):
        """get_database_url() should rewrite postgresql:// to postgresql+psycopg://."""
        url = "postgresql://user:pass@host:5432/db"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = get_database_url()
        assert result == "postgresql+psycopg://user:pass@host:5432/db"

    def test_passes_through_psycopg_url_unchanged(self):
        """A URL already using +psycopg should not be modified."""
        url = "postgresql+psycopg://user:pass@host:5432/db"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = get_database_url()
        assert result == url

    def test_passes_through_other_schemes_unchanged(self):
        """Non-postgresql schemes (e.g. sqlite) should pass through."""
        url = "sqlite:///tmp/test.db"
        with patch.dict(os.environ, {"DATABASE_URL": url}):
            result = get_database_url()
        assert result == url


# ---------------------------------------------------------------------------
# get_engine()
# ---------------------------------------------------------------------------


class TestGetEngine:
    def test_creates_async_engine_with_explicit_url(self):
        """get_engine(url=...) should create an AsyncEngine without reading env."""
        with patch("koinonia_db.engine.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            result = get_engine(url="postgresql+psycopg://localhost/test")

            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[0][0] == "postgresql+psycopg://localhost/test"
            assert result is mock_engine

    def test_returns_singleton(self):
        """Calling get_engine() twice should return the same instance."""
        with patch("koinonia_db.engine.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            first = get_engine(url="postgresql+psycopg://localhost/test")
            second = get_engine(url="postgresql+psycopg://localhost/other")

            assert first is second
            assert mock_create.call_count == 1

    def test_falls_back_to_env_url(self):
        """get_engine() without url= should read DATABASE_URL from environment."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            with patch("koinonia_db.engine.create_async_engine") as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine

                get_engine()

                call_args = mock_create.call_args
                # Should have been converted to +psycopg by get_database_url()
                assert call_args[0][0] == "postgresql+psycopg://localhost/test"

    def test_passes_pool_settings(self):
        """get_engine() should configure pool_size and max_overflow."""
        with patch("koinonia_db.engine.create_async_engine") as mock_create:
            mock_create.return_value = MagicMock()

            get_engine(url="postgresql+psycopg://localhost/test")

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["pool_size"] == 5
            assert call_kwargs["max_overflow"] == 10


# ---------------------------------------------------------------------------
# get_session_factory()
# ---------------------------------------------------------------------------


class TestGetSessionFactory:
    def test_returns_async_sessionmaker(self):
        """get_session_factory() should return an async_sessionmaker instance."""
        with patch("koinonia_db.engine.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            factory = get_session_factory(engine=mock_engine)

            # async_sessionmaker is callable and has a class_ attribute
            assert callable(factory)

    def test_uses_provided_engine(self):
        """get_session_factory(engine=...) should bind to the given engine."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        mock_engine = MagicMock()
        factory = get_session_factory(engine=mock_engine)

        assert isinstance(factory, async_sessionmaker)

    def test_falls_back_to_singleton_engine(self):
        """get_session_factory() without engine= should use get_engine()."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            with patch("koinonia_db.engine.create_async_engine") as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine

                engine_module._engine = None
                factory = get_session_factory()

                # get_engine() should have been called internally
                mock_create.assert_called_once()
                assert callable(factory)


# ---------------------------------------------------------------------------
# dispose_engine()
# ---------------------------------------------------------------------------


class TestDisposeEngine:
    @pytest.mark.asyncio
    async def test_disposes_and_resets_singleton(self):
        """dispose_engine() should call engine.dispose() and set _engine to None."""
        mock_engine = AsyncMock()
        engine_module._engine = mock_engine

        await dispose_engine()

        mock_engine.dispose.assert_awaited_once()
        assert engine_module._engine is None

    @pytest.mark.asyncio
    async def test_noop_when_no_engine(self):
        """dispose_engine() should do nothing if no engine was created."""
        engine_module._engine = None

        await dispose_engine()  # should not raise

        assert engine_module._engine is None

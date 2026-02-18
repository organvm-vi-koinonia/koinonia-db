# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-02-17

### Added
- **AQUA COMMUNIS sprint** — shared syllabus service
- `koinonia_db.syllabus_service` module with `generate_learning_path()` — extracted from community-hub for shared use
- `generate_learning_path` re-exported from `koinonia_db.__init__`
- 3 new tests: service importable, ORGAN_MAP validation, top-level re-export

## [0.3.0] - 2026-02-17

### Added
- **IGNIS KOINOS sprint** — full-text search + syllabus schema
- Alembic migration `002_fulltext_search.py` — tsvector columns + GIN indexes on sessions, segments, entries, taxonomy_nodes
- Alembic migration `003_syllabus_tables.py` — syllabus schema with learner_profiles, learning_paths, learning_modules
- SQLAlchemy models: `LearnerProfileRow`, `LearningPathRow`, `LearningModuleRow`
- Idempotent UPSERT seed script (`seed_all.py`) using natural keys

## [0.2.0] - 2026-02-17

### Added
- Initial schema: salons, reading, community (Alembic migration `001_initial_schema.py`)
- SQLAlchemy ORM models for all three schemas
- Async engine support via `koinonia_db.engine`
- Master seed script (`scripts/seed_all.py`) with taxonomy, salons, readings, curricula, community
- Seed data: 40+ taxonomy nodes, 5 salons, 39 reading entries, 3 curricula, 3 events
- CI workflow and README

## [0.1.0] - 2026-02-17

### Added
- Initial package structure
- `Base` and `TimestampMixin` for model declarations

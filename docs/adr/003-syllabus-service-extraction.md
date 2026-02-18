# ADR-003: Syllabus Service Extraction

**Status:** Accepted
**Date:** 2026-02-17
**Context:** AQUA COMMUNIS Sprint — Batch 4

## Context

The learning path generation logic existed in two places:
1. `community-hub/routes/syllabus.py` — the `_generate_path()` function (~100 lines)
2. `adaptive-personal-syllabus/db_generator.py` — the `DatabaseSyllabusGenerator` class

Both read the same taxonomy/readings from the same database and produce learning paths. The community-hub version was an async copy of the logic.

## Decision

Extract the generation logic into `koinonia_db.syllabus_service.generate_learning_path()` as a shared async service:

- Lives in `koinonia-db` since it depends only on koinonia-db models
- Re-exported from `koinonia_db.__init__` for convenience
- `community-hub/routes/syllabus.py` imports from the service instead of defining its own
- Constants (`ORGAN_MAP`, `DIFFICULTY_ORDER`) moved to the service module

## Consequences

**Pros:**
- Single source of truth for generation logic
- `syllabus.py` reduced from 237 to 107 lines (route handlers only)
- Any future consumer of learning path generation gets the same logic

**Cons:**
- `koinonia-db` now has a "service" module beyond just models/engine, slightly expanding its scope
- The async service commits the transaction — callers must be aware they're passing a session that will be committed

**Alternative considered:** A separate `koinonia-services` package. Rejected as premature — one service function doesn't warrant a new package.

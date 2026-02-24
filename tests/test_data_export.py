"""Tests for koinonia_db.data_export — schema manifest generation."""
import json
from pathlib import Path

from koinonia_db.data_export import (
    build_manifest,
    export_schema_manifest,
    export_seed_manifest,
    main,
    ALL_MODELS,
)


SEED_DIR = Path(__file__).parent.parent / "seed"


def test_all_models_registered():
    """Every declared model class appears in ALL_MODELS."""
    assert len(ALL_MODELS) == 16


def test_schema_manifest_has_models():
    """export_schema_manifest returns info for all models."""
    result = export_schema_manifest()
    assert result["model_count"] == 16
    names = [m["class_name"] for m in result["models"]]
    assert "SalonSessionRow" in names
    assert "Curriculum" in names
    assert "LearningPathRow" in names


def test_schema_manifest_column_info():
    """Each model has columns with expected keys."""
    result = export_schema_manifest()
    for model in result["models"]:
        assert model["column_count"] > 0
        for col in model["columns"]:
            assert "name" in col
            assert "type" in col
            assert "nullable" in col
            assert "primary_key" in col


def test_schema_manifest_schemas():
    """Schema names include our four DB schemas."""
    result = export_schema_manifest()
    schemas = result["schemas"]
    assert "salons" in schemas
    assert "reading" in schemas
    assert "community" in schemas
    assert "syllabus" in schemas


def test_seed_manifest_with_real_seed():
    """Seed manifest correctly inventories the actual seed directory."""
    result = export_seed_manifest(SEED_DIR)
    assert result["total_seed_entries"] > 0
    assert "sample_sessions.json" in result["seed_files"]
    assert "curricula.json" in result["seed_files"]
    assert "taxonomy.json" in result["seed_files"]
    assert result["seed_files"]["sample_sessions.json"]["entries"] >= 2


def test_seed_manifest_missing_dir(tmp_path):
    """Seed manifest handles a nonexistent directory gracefully."""
    result = export_seed_manifest(tmp_path / "nonexistent")
    assert result["total_seed_entries"] == 0
    assert result["seed_files"] == {}


def test_build_manifest_structure():
    """build_manifest returns all expected top-level keys."""
    result = build_manifest(SEED_DIR)
    assert "generated_at" in result
    assert "package_version" in result
    assert "model_count" in result
    assert "models" in result
    assert "model_details" in result
    assert "schemas" in result
    assert "seed_files" in result
    assert "total_seed_entries" in result
    assert isinstance(result["models"], list)
    assert isinstance(result["model_details"], list)


def test_main_writes_file(tmp_path):
    """main() writes schema-manifest.json to the output directory."""
    out = main(output_dir=tmp_path, seed_dir=SEED_DIR)
    assert out.exists()
    assert out.name == "schema-manifest.json"
    data = json.loads(out.read_text())
    assert data["model_count"] == 16
    assert data["total_seed_entries"] > 0

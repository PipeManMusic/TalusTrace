import pytest
from pathlib import Path
from infra.persistence import JSONPersistence
from core.models import Harness

def test_json_import_export_round_trip(tmp_path):
    file_path = tmp_path / "round_trip_test.json"
    harness = Harness()
    expected_name = "JSON-Round-Trip-Validation-Harness"
    harness.meta["name"] = expected_name

    # Export to JSON
    JSONPersistence.save(harness, file_path)
    assert file_path.exists(), "JSON file was not created."

    # Import from JSON
    loaded = JSONPersistence.load(file_path)
    assert loaded.meta["name"] == expected_name

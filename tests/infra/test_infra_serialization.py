import pytest
import ast
from pathlib import Path
from infra.context import ProjectContext
from core.models import Harness

def test_enforce_serialization_folder_locations():
    """
    Enforces Phase 1-3.1: Ensures Serialization/State logic is in /core or /infra,
    never in /ui, as per talus_trace_codebase_architecture.md.
    """
    project_root = Path(__file__).parent.parent
    
    # 1. Validate mandated folder existence
    assert (project_root / "core").exists(), "Missing /core directory for headless logic."
    assert (project_root / "infra").exists(), "Missing /infra directory for system services."
    assert (project_root / "ui").exists(), "Missing /ui directory for view layer."

    # 2. Validate Serialization logic is NOT in the UI folder
    ui_files = list((project_root / "ui").glob("**/*.py"))
    for ui_file in ui_files:
        with open(ui_file, "r", encoding="utf-8") as f:
            content = f.read()
            # UI should not contain the primary save/load implementation logic
            assert "def save_as" not in content, f"Violation: Serialization logic found in UI file {ui_file.name}"

def test_core_serialization_round_trip(tmp_path):
    """
    Validates the Round-Trip integrity required by Phase 1-3.1.
    Ensures Harness data remains 'Holy' through a save/load cycle.
    """
    test_file = tmp_path / "round_trip_test.yaml"
    ctx = ProjectContext()
    
    # Set unique metadata to verify persistence
    expected_name = "Round-Trip-Validation-Harness"
    ctx.harness.meta["name"] = expected_name
    
    # Save via Core/Infra logic
    ctx.save_as(test_file)
    assert test_file.exists(), "YAML file was not created by ProjectContext."
    
    # Reload into a fresh context
    new_ctx = ProjectContext()
    new_ctx.load(test_file)
    
    # Assert data integrity
    assert new_ctx.harness.meta["name"] == expected_name
    assert new_ctx.dirty is False, "Context should be clean immediately after loading."

def test_core_dependency_isolation():
    """
    Validates 'Core is Holy': Core files must NOT import UI libraries.
    Ensures ProjectState remains headless.
    """
    project_root = Path(__file__).parent.parent
    core_path = project_root / "core"
    forbidden = {"PySide6", "PyQt6", "ui"}

    for py_file in core_path.glob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [alias.name.split('.')[0] for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module, asname=None)])]
                for mod in modules:
                    assert mod not in forbidden, f"Architecture Violation in {py_file.name}: Core imports {mod}."
import pytest
import ast
from pathlib import Path

# Mandated directory structure based on the corrected /core path
REQUIRED_FOLDERS = [
    "core",   # Pure Python Data Models (formerly backend)
    "infra",  # System Services (IO, Commands)
    "ui",     # Qt/PySide6 View Layer
]

def test_enforce_folder_structure():
    """
    Validates that the project adheres to the directory structure defined in 
    talus_trace_codebase_architecture.md.
    """
    project_root = Path(__file__).parent.parent
    for folder in REQUIRED_FOLDERS:
        assert (project_root / folder).exists(), f"Missing required architecture folder: {folder}"

def test_enforce_core_isolation():
    """
    Validates 'Core is Holy' rule: Core files must NOT import UI or Infra libraries.
    This ensures serialization and engineering math remain headless.
    """
    project_root = Path(__file__).parent.parent
    core_path = project_root / "core"
    
    # UI and Infra are strictly forbidden inside the Core
    forbidden_imports = {"PySide6", "PyQt6", "ui", "infra"}

    for py_file in core_path.glob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            # Check 'import PySide6'
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split('.')[0]
                    assert root_module not in forbidden_imports, \
                        f"Architecture Violation in {py_file.name}: Core cannot import '{alias.name}'"
            
            # Check 'from PySide6 import ...'
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split('.')[0]
                    assert root_module not in forbidden_imports, \
                        f"Architecture Violation in {py_file.name}: Core cannot import from '{node.module}'"

def test_infra_serialization_location():
    """
    Enforces that ProjectState logic resides in core/ or infra/, 
    never in the UI layer.
    """
    project_root = Path(__file__).parent.parent
    # Based on the correction, models and context should be in /core
    assert (project_root / "core/models.py").exists(), "Models must be in /core"
    assert (project_root / "core/context.py").exists() or (project_root / "talustrace/backend/context.py").exists(), \
        "ProjectContext (Serialization) must be in a headless directory"
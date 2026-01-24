import pytest
from pathlib import Path
from api.manager import APIManager  # Implementation assumes this location

def test_api_is_singleton():
    """
    Validates Phase 1-3.1: PI (Public Interface) Implement Singleton Accessor.
    Ensures that multiple calls to the API accessor return the same instance.
    """
    # Attempt to get the singleton instance twice
    api1 = APIManager.get_instance()
    api2 = APIManager.get_instance()
    
    # Assert they are the exact same object in memory
    assert api1 is api2, "APIManager failed singleton validation: Instances are not identical."

def test_api_folder_location():
    """
    Enforces that the API layer is located in the mandated /api directory
    separate from /core and /ui.
    """
    project_root = Path(__file__).parent.parent.parent
    api_dir = project_root / "api"
    manager_path = api_dir / "manager.py"
    assert api_dir.exists(), "Architecture Violation: Missing /api directory."
    assert manager_path.exists(), "Architecture Violation: API singleton must be in /api/manager.py."

def test_api_core_access():
    """
    Ensures the API singleton has access to the ProjectContext (Source of Truth)
    without violating layer isolation.
    """
    api = APIManager.get_instance()
    
    # The API should be the gateway to the core's ProjectContext
    assert hasattr(api, 'context'), "API Singleton must hold a reference to the ProjectContext."
    from infra.context import ProjectContext
    assert isinstance(api.context, ProjectContext), "API context must be an instance of ProjectContext."
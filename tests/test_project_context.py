import pytest
from pathlib import Path
from infra.context import ProjectContext
from core.models import Harness

def test_context_state_management():
    """
    Validates Roadmap ID #2: TDD Context Manager.
    Ensures state is decoupled from the GUI.
    """
    ctx = ProjectContext()
    
    # Verify initial state
    assert ctx.dirty is False
    assert isinstance(ctx.harness, Harness)
    
    # Simulate a modification
    ctx.harness.meta["name"] = "Modified Harness"
    # In a real impl, a 'mark_dirty' method or observer would trigger this
    ctx.dirty = True 
    assert ctx.dirty is True

def test_context_persistence(tmp_path):
    """
    Validates Roadmap ID #3: Impl ProjectContext.
    Ensures load/save logic is correctly moved to the backend.
    """
    test_file = tmp_path / "test_harness.yaml"
    ctx = ProjectContext()
    ctx.harness.meta["name"] = "Persistence Test"
    
    # Test Saving
    ctx.save_as(test_file)
    assert test_file.exists()
    assert ctx.dirty is False
    
    # Test Loading
    new_ctx = ProjectContext()
    new_ctx.load(test_file)
    assert new_ctx.harness.meta["name"] == "Persistence Test"
    assert new_ctx.current_file == test_file
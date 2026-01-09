import pytest
from api.actions import registry
from infra.context import ProjectContext

def test_file_new_clears_state():
    """PH5-5.7: File > New should reset harness and undo stack."""
    ctx = ProjectContext()
    ctx.harness.meta["project"] = "Old Project"
    ctx.is_dirty = True
    
    # Simulate 'File New' Action logic
    ctx.new_project()
    
    assert ctx.harness.meta.get("project") != "Old Project"
    assert len(ctx.harness.devices) == 0
    assert ctx.is_dirty is False
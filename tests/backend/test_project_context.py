import pytest
from talustrace.backend.context import ProjectContext
from talustrace.backend.models import Harness
from pathlib import Path

def test_project_context_initialization():
    ctx = ProjectContext()
    assert isinstance(ctx.harness, Harness)
    assert ctx.dirty is False

def test_save_load_cycle(tmp_path):
    """
    Verify we can save the harness to disk and load it back.
    Note: We expect the loaded object to be a base 'Harness', 
    but with identical data to our input.
    """
    ctx = ProjectContext()
    fpath = tmp_path / "test_harness.yaml"
    ctx.save_as(fpath)
    assert fpath.exists()
    new_context = ProjectContext()
    new_context.load(fpath)
    original_data = ctx.harness.model_dump()
    loaded_data = new_context.harness.model_dump()
    assert original_data == loaded_data
    assert new_context.current_file == fpath
    assert not new_context.dirty

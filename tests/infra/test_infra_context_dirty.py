import tempfile
import os
import pytest
from infra.context import Context

class DummyHarness:
    def __init__(self):
        self.meta = {}
        self._rev = 0
    def increment_revision(self):
        self._rev += 1
    def to_dict(self):
        return {'meta': self.meta, 'rev': self._rev}
    @classmethod
    def from_dict(cls, d):
        h = cls()
        h.meta = d.get('meta', {})
        h._rev = d.get('rev', 0)
        return h

def test_dirty_flag_on_mutation_and_save(monkeypatch):
    ctx = Context()
    # Patch harness to dummy
    ctx.harness = DummyHarness()
    # Should start clean
    assert ctx.is_dirty is False
    # Mark dirty
    ctx.mark_dirty()
    assert ctx.is_dirty is True
    # Mark clean
    ctx.mark_clean()
    assert ctx.is_dirty is False
    # Set dirty via property
    ctx.is_dirty = True
    assert ctx.dirty is True
    ctx.is_dirty = False
    assert ctx.dirty is False

def test_dirty_flag_on_save_and_load(tmp_path, monkeypatch):
    ctx = Context()
    ctx.harness = DummyHarness()
    ctx.mark_dirty()
    assert ctx.is_dirty is True
    # Patch harness methods for save/load
    ctx.harness.to_dict = lambda: {'meta': {}, 'rev': 1}
    ctx.harness.increment_revision = lambda: None
    # Save should clear dirty
    save_path = tmp_path / 'test.yaml'
    ctx.save_as(save_path)
    assert ctx.is_dirty is False
    # Mark dirty again
    ctx.mark_dirty()
    assert ctx.is_dirty is True
    # Patch from_dict for load
    DummyHarness.from_dict = classmethod(lambda cls, d: DummyHarness())
    # Write a dummy file
    with open(save_path, 'w') as f:
        f.write('meta: {}\nrev: 1\n')
    # Load should clear dirty
    ctx.load(save_path)
    assert ctx.is_dirty is False

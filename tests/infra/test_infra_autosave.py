import os
import tempfile
import pytest
from infra.context import Context
from api import actions

class DummyHarness:
    def __init__(self, name):
        self.meta = {'name': name}
    def to_dict(self):
        return {'meta': self.meta}
    @classmethod
    def from_dict(cls, d):
        return cls(d['meta']['name'])

def test_autosave_and_restore(tmp_path, monkeypatch):
    ctx = Context()
    ctx.harness = DummyHarness('autosave-test')
    # Patch harness methods
    monkeypatch.setattr(ctx, 'harness', DummyHarness('autosave-test'))
    monkeypatch.setattr(ctx, 'harness', ctx.harness)
    # Patch context to use DummyHarness
    monkeypatch.setattr('infra.context.Harness', DummyHarness)
    # Autosave
    autosave_path = ctx.autosave(directory=tmp_path)
    assert autosave_path.exists()
    # Change harness
    ctx.harness = DummyHarness('changed')
    # Restore
    ctx.restore_autosave(directory=tmp_path)
    assert ctx.harness.meta['name'] == 'autosave-test'
    # Clear autosave
    ctx.clear_autosave(directory=tmp_path)
    assert not autosave_path.exists()

def test_api_autosave_and_restore(tmp_path, monkeypatch):
    # Patch global context
    ctx = Context()
    ctx.harness = DummyHarness('api-autosave')
    monkeypatch.setattr('infra.context.Harness', DummyHarness)
    monkeypatch.setattr('infra.context.global_context', ctx)
    # Autosave via API
    path = actions.autosave_project()
    assert os.path.basename(str(path)) == '.autosave.yaml'
    # Change harness
    ctx.harness = DummyHarness('changed')
    # Restore via API
    actions.restore_session()
    assert ctx.harness.meta['name'] == 'api-autosave'
    # Cleanup
    ctx.clear_autosave()

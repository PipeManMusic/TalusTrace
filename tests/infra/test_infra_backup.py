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

def test_backup_and_restore(tmp_path, monkeypatch):
    ctx = Context()
    ctx.harness = DummyHarness('backup-test')
    monkeypatch.setattr('infra.context.Harness', DummyHarness)
    # Backup
    backup_path = ctx.backup_project(directory=tmp_path)
    assert backup_path.exists()
    # Change harness
    ctx.harness = DummyHarness('changed')
    # Restore
    ctx.restore_backup(backup_path)
    assert ctx.harness.meta['name'] == 'backup-test'
    # List backups
    backups = ctx.list_backups(directory=tmp_path)
    assert backup_path in backups

def test_backup_rotation(tmp_path, monkeypatch):
    ctx = Context()
    ctx.BACKUP_LIMIT = 3
    monkeypatch.setattr('infra.context.Harness', DummyHarness)
    # Create 5 backups
    import time
    for i in range(5):
        ctx.harness = DummyHarness(f'b{i}')
        ctx.backup_project(directory=tmp_path)
        time.sleep(1)
    backups = ctx.list_backups(directory=tmp_path)
    assert len(backups) == 3
    # Newest backup should be last created
    assert backups[0].read_text().find('b4') != -1

def test_api_backup_and_restore(tmp_path, monkeypatch):
    ctx = Context()
    ctx.harness = DummyHarness('api-backup')
    monkeypatch.setattr('infra.context.Harness', DummyHarness)
    monkeypatch.setattr('infra.context.global_context', ctx)
    # Backup via API
    backup_path = actions.backup_project()
    assert os.path.basename(str(backup_path)).startswith('backup_')
    # Change harness
    ctx.harness = DummyHarness('changed')
    # Restore via API
    actions.restore_backup(backup_path)
    assert ctx.harness.meta['name'] == 'api-backup'

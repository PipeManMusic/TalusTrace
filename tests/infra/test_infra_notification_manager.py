import pytest
from infra.notification_manager import NotificationManager
import tempfile
import os
import json

def test_notification_manager(tmp_path):
    log_path = tmp_path / 'notifications.log'
    dispatched = []
    def hook(entry):
        dispatched.append(entry)
    mgr = NotificationManager(log_path, dispatch_hooks=[hook])
    mgr.notify('info', 'Test info')
    mgr.notify('warning', 'Test warning', code=123)
    notes = list(mgr.list_notifications())
    assert len(notes) == 2
    assert notes[0]['level'] == 'info'
    assert notes[1]['level'] == 'warning'
    assert notes[1]['code'] == 123
    # Check dispatch hook
    assert len(dispatched) == 2
    assert dispatched[1]['message'] == 'Test warning'
    # Check log file
    with open(log_path) as f:
        lines = f.readlines()
    assert len(lines) == 2
    entries = [json.loads(line) for line in lines]
    assert entries[0]['event_type'] == 'notification'
    assert entries[1]['payload']['message'] == 'Test warning'
    # Test persisted notification retrieval
    persisted = list(mgr.list_notifications(persisted=True))
    assert any(n['message'] == 'Test info' for n in persisted)
    # Clear in-memory and persisted notifications
    mgr.clear_notifications(persisted=True)
    assert list(mgr.list_notifications()) == []
    assert list(mgr.list_notifications(persisted=True)) == []

import pytest
from infra.notification_manager import NotificationManager
from infra.error_handler import CentralErrorHandler
import tempfile
import json

def test_central_error_handler(tmp_path):
    log_path = tmp_path / 'errors.log'
    note_mgr = NotificationManager(tmp_path / 'notes.log')
    handler = CentralErrorHandler(note_mgr, log_path)
    # Simulate error
    try:
        raise ValueError('Test error!')
    except Exception as e:
        handler.handle_exception(e, context='unit test')
    # Check error log
    with open(log_path) as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry['event_type'] == 'error'
    assert 'Test error!' in entry['payload']['message']
    # Check notification
    notes = list(note_mgr.list_notifications())
    assert notes[0]['level'] == 'error'
    assert 'Test error!' in notes[0]['message']
    assert 'unit test' in notes[0]['context']

    # Test decorator
    @handler.catch_errors
    def fail():
        raise RuntimeError('Decorated error')
    with pytest.raises(RuntimeError):
        fail()
    # Should log the decorated error too
    with open(log_path) as f:
        lines = f.readlines()
    assert any('Decorated error' in json.loads(line)['payload']['message'] for line in lines)

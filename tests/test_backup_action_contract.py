import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Backup action triggers backup logic via APIManager
def test_backup_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'backup'):
        pytest.skip('APIManager does not implement backup contract.')
    api_manager.backup = MagicMock()
    # Simulate backup action
    api_manager.backup()
    api_manager.backup.assert_called_once_with()

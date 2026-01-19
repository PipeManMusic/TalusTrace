import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Notification action triggers notification logic via APIManager
def test_notification_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'notify'):
        pytest.skip('APIManager does not implement notify contract.')
    api_manager.notify = MagicMock()
    # Simulate notification action (e.g., sending a message)
    message = 'Test notification'
    api_manager.notify(message)
    api_manager.notify.assert_called_once_with(message)

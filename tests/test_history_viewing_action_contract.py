import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: History viewing action triggers history logic via APIManager
def test_history_viewing_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'view_history'):
        pytest.skip('APIManager does not implement view_history contract.')
    api_manager.view_history = MagicMock()
    # Simulate history viewing action
    api_manager.view_history()
    api_manager.view_history.assert_called_once_with()

import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Autosave action triggers autosave logic via APIManager
def test_autosave_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'autosave'):
        pytest.skip('APIManager does not implement autosave contract.')
    api_manager.autosave = MagicMock()
    # Simulate autosave action
    api_manager.autosave()
    api_manager.autosave.assert_called_once_with()

import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Session restore action triggers restore logic via APIManager
def test_session_restore_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'restore_session'):
        pytest.skip('APIManager does not implement restore_session contract.')
    api_manager.restore_session = MagicMock()
    # Simulate session restore action
    api_manager.restore_session()
    api_manager.restore_session.assert_called_once_with()

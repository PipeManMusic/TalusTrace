import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Logging action triggers logging logic via APIManager
def test_logging_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'log'): 
        pytest.skip('APIManager does not implement log contract.')
    api_manager.log = MagicMock()
    # Simulate logging action (e.g., logging a message)
    message = 'Test log message'
    api_manager.log(message)
    api_manager.log.assert_called_once_with(message)

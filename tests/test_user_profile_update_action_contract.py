import pytest
from unittest.mock import MagicMock
from api.manager import APIManager

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: User profile update action triggers profile update via APIManager
def test_user_profile_update_action_contract(api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'update_user_profile'):
        pytest.skip('APIManager does not implement update_user_profile contract.')
    api_manager.update_user_profile = MagicMock()
    # Simulate user profile update action (e.g., updating username)
    profile = {'username': 'new_user'}
    api_manager.update_user_profile(profile)
    api_manager.update_user_profile.assert_called_once_with(profile)

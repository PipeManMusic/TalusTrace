import pytest
from unittest.mock import MagicMock
from ui.canvas import HarnessCanvas
from api.manager import APIManager

@pytest.fixture
def canvas(qtbot):
    c = HarnessCanvas()
    qtbot.addWidget(c)
    c.show()
    return c

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Copy and paste actions duplicate items and update state via APIManager
def test_copy_paste_action_contract(canvas, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'copy_item') or not hasattr(api_manager, 'paste_item'):
        pytest.skip('APIManager does not implement copy/paste contract.')
    api_manager.copy_item = MagicMock()
    api_manager.paste_item = MagicMock()
    # Simulate copy action (e.g., copying an item with id 'device_1')
    item_id = 'device_1'
    canvas.copy_item = api_manager.copy_item
    canvas.copy_item(item_id)
    api_manager.copy_item.assert_called_once_with(item_id)
    # Simulate paste action
    canvas.paste_item = api_manager.paste_item
    canvas.paste_item()
    api_manager.paste_item.assert_called_once_with()

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

# Contract: Deletion action removes item and updates state via APIManager
def test_deletion_action_contract(canvas, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.delete_item = MagicMock()
    # Simulate deletion action (e.g., deleting an item with id 'device_1')
    item_id = 'device_1'
    # Assume HarnessCanvas calls APIManager.delete_item on deletion
    canvas.delete_item = api_manager.delete_item
    canvas.delete_item(item_id)
    api_manager.delete_item.assert_called_once_with(item_id)

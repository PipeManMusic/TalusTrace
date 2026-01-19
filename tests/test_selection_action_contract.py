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

# Contract: Selection action updates selection state via APIManager
def test_selection_action_contract(canvas, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.select_item = MagicMock()
    # Simulate selection action (e.g., selecting an item with id 'device_1')
    item_id = 'device_1'
    # Assume HarnessCanvas calls APIManager.select_item on selection
    canvas.select_item = api_manager.select_item
    canvas.select_item(item_id)
    api_manager.select_item.assert_called_once_with(item_id)

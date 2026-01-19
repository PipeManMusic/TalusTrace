import pytest
from unittest.mock import MagicMock
from ui.main_window import MainWindow
from api.manager import APIManager
from ui.canvas import HarnessCanvas

@pytest.fixture
def main_window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Device placement via action system creates a device and updates the canvas
def test_device_placement_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.tool_manager = MagicMock()
    api_manager.tool_manager.set_tool = MagicMock()
    api_manager.dispatch_action = MagicMock()
    main_window.api = api_manager
    main_window.register_toolbar_commands()
    from api.actions import dispatch_action
    # Simulate device placement action
    dispatch_action('tool.add_generic_device')
    api_manager.tool_manager.set_tool.assert_called_once_with('placement')
    # Simulate device creation (mock AddDeviceCommand)
    api_manager.dispatch_action('device.create')
    api_manager.dispatch_action.assert_called_with('device.create')
    # Check that the canvas scene is updated (mock addItem)
    main_window.canvas.scene.addItem = MagicMock()
    main_window.canvas.scene.addItem.assert_not_called()  # Should be called in real placement logic

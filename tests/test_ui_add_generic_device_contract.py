import pytest
from api.manager import APIManager
from ui.main_window import MainWindow
from PySide6.QtCore import Qt

def test_ui_add_generic_device_contract(qtbot):
    """
    Contract test: Simulate adding a generic device via the UI/tool and assert only one device is added,
    and only via AddDeviceCommand (enforced by fixture).
    """
    APIManager.reset()
    api = APIManager.get_instance()
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    # Simulate activating the placement tool and adding a device
    # (You may need to adapt this to your actual UI/tool activation logic)
    api.tool_manager.set_tool("placement")
    canvas = win.canvas
    # Simulate a mouse click to place a device
    pos = canvas.mapToScene(100, 100)
    qtbot.mouseClick(canvas.viewport(), Qt.LeftButton, pos=canvas.mapFromScene(pos))
    # Assert only one device was added (fixture will enforce contract)
    assert len(api.context.harness.devices) == 1, "More than one device added for a single UI action!"

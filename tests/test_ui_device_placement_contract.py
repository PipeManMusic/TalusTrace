import pytest
from unittest.mock import patch
from PySide6.QtCore import QPointF
from ui.main_window import MainWindow
from api.manager import APIManager

def test_device_placement_uses_adddevicecommand(qtbot):
    """
    Contract: Placing a device via the UI must use AddDeviceCommand and the undo stack.
    This ensures all device creation is undoable and routed through the correct API/infra layer.
    """
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = window.api
    # Activate placement tool
    api.tool_manager.set_tool("placement")
    placement_tool = api.tool_manager.get_tool("placement")
    # Patch AddDeviceCommand and undo_stack.push
    with patch("api.commands.device.AddDeviceCommand.__init__", return_value=None) as cmd_init, \
         patch.object(api.context.undo_stack, "push") as push_mock:
        # Simulate device placement via PlacementTool
        scene_pos = QPointF(100, 100)
        placement_tool.start_drag(None, scene_pos)
        # Simulate mouse press to commit placement
        class DummyEvent:
            def __init__(self, x, y):
                self.x = lambda: x
                self.y = lambda: y
                self.button = lambda: 1  # Qt.LeftButton
                self.scene_pos = QPointF(x, y)
        placement_tool.on_mouse_press(DummyEvent(100, 100))
        # Assert AddDeviceCommand was constructed and pushed to undo stack
        assert cmd_init.called, "AddDeviceCommand was not used for device placement!"
        assert push_mock.called, "Undo stack was not used for device placement!"

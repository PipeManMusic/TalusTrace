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
    canvas = window.canvas
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPoint, QEvent, Qt
    input_system = api.input_system
    input_system.install(canvas)
    with patch("api.commands.device.AddDeviceCommand.__init__", return_value=None) as cmd_init, \
         patch.object(api.context.undo_stack, "push") as push_mock:
        # Simulate mouse press event routed through InputSystem
        view_pos = canvas.mapFromScene(canvas.mapToScene(100, 100))
        event = QMouseEvent(QEvent.MouseButtonPress, view_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        input_system.eventFilter(canvas, event)
        # Assert AddDeviceCommand was constructed and pushed to undo stack
        assert cmd_init.called, "AddDeviceCommand was not used for device placement!"
        assert push_mock.called, "Undo stack was not used for device placement!"

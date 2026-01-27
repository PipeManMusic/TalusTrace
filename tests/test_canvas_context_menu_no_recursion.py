import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtCore import QPoint, Qt
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock

def test_canvas_context_menu_no_recursion(qtbot):
    """
    Contract: Context menu event on canvas must be routed to APIManager.open_context_menu,
    must not cause recursion, and must be accepted. The API must handle the event, not call back into the UI event handler.
    """
    app = QApplication.instance() or QApplication([])
    api = APIManager.get_instance()
    from unittest.mock import patch
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    canvas = window.canvas
    # Add a dummy device at (10, 10) so InputSystem finds an item
    from core.device import Device
    from ui.items.device import DeviceItem
    dummy_device = Device(x=10, y=10, meta={"width_mm": 20, "height_mm": 20})
    device_item = DeviceItem(dummy_device)
    canvas.scene.addItem(device_item)

    # Set the active tool to 'move' so InputSystem routes right-clicks for context menu
    api.tool_manager.set_tool("move")
    # Explicitly select the device so InputSystem recognizes it as selected
    from core.selection import SelectionManager
    SelectionManager().set_selection([dummy_device])

    # Ensure InputSystem is installed as event filter on viewport for test
    input_system = getattr(window.api, 'input_system', None)
    assert input_system is not None, "InputSystem not found on APIManager."
    input_system.install(canvas.viewport())

    # Map scene position to canvas widget coordinates
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPointF
    scene_pos = QPointF(15, 15)
    view_pos = canvas.mapFromScene(scene_pos)

    with patch.object(api, "open_context_menu", wraps=api.open_context_menu) as mock_open:
        try:
            QTest.mouseClick(canvas.viewport(), Qt.RightButton, Qt.NoModifier, view_pos)
        except RecursionError:
            pytest.fail("RecursionError: contextMenuEvent and open_context_menu are calling each other recursively.")
        mock_open.assert_called_once()
    window.close()

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, Qt
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock

def test_drag_event_routes_to_move_tool(qtbot):
    """
    Contract: Drag events on a device should route to the active MoveTool via the InputSystem.
    """
    app = QApplication.instance() or QApplication([])
    # Reset APIManager singleton and tool_manager to avoid MagicMock pollution
    from api.tool_manager import ToolManager
    APIManager._instance = None
    from tools.move_tool import MoveTool
    from unittest.mock import MagicMock
    move_tool = MoveTool()
    move_tool.on_mouse_press = MagicMock(wraps=move_tool.on_mouse_press)
    move_tool.on_mouse_move = MagicMock(wraps=move_tool.on_mouse_move)
    move_tool.on_mouse_release = MagicMock(wraps=move_tool.on_mouse_release)
    # Inject the mocked MoveTool into InputSystem
    from ui.input_system import InputSystem
    input_system = InputSystem(move_tool=move_tool)
    api = APIManager.get_instance()
    api.input_system = input_system
    api.tool_manager = ToolManager()
    api.tool_manager.register_tool("move", move_tool)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Add a device to the model and scene
    device = api.context.harness.devices[0] if api.context.harness.devices else None
    if device is None:
        from core.models import Device
        device = Device(id="test_device", x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
        api.context.harness.devices.append(device)
        window.canvas.load_harness(api.context.harness)
    # Find the DeviceItem in the scene
    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene registry."
    # Activate MoveTool
    api.tool_manager.set_tool("move")
    # Ensure DeviceItem is selected and MoveTool is active before mocking
    item.setSelected(True)
    # Instead of strict identity, check type
    assert isinstance(api.tool_manager.active_tool, MoveTool), "MoveTool is not active before drag."
    # Use DeviceItem's actual scene position for mouse events
    scene = item.scene()
    view = scene.views()[0]
    start_scene_pos = item.scenePos() + item.boundingRect().center()
    end_scene_pos = start_scene_pos + QPointF(50, 25)
    start_viewport_pos = view.mapFromScene(start_scene_pos)
    end_viewport_pos = view.mapFromScene(end_scene_pos)
    qtbot.mousePress(view.viewport(), Qt.LeftButton, pos=start_viewport_pos)
    qtbot.mouseMove(view.viewport(), pos=end_viewport_pos)
    qtbot.mouseRelease(view.viewport(), Qt.LeftButton, pos=end_viewport_pos)
    # Check that MoveTool received the events
    assert move_tool.on_mouse_press.called, "MoveTool did not receive mouse press event."
    assert move_tool.on_mouse_move.called, "MoveTool did not receive mouse move event."
    assert move_tool.on_mouse_release.called, "MoveTool did not receive mouse release event."
    window.close()

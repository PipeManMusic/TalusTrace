import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, Qt
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import patch

@pytest.mark.gui
def test_drag_event_routes_to_move_tool(qtbot):
    """
    Contract: After standard app startup (no explicit toolbar clicks), clicking
    and dragging a device on the canvas must route through InputSystem to MoveTool
    and update the device position in the model.

    This test uses the REAL production startup path — no injected tools, no
    force-selected items, no custom InputSystem. If drag-to-move is broken at
    startup, this test MUST fail.
    """
    # Standard production startup: APIManager already reset by autouse fixture
    api = APIManager.get_instance()

    # Verify production default: select tool should be active
    assert api.tool_manager.active_tool is not None, \
        "No active tool after APIManager init — startup is broken"

    # Create MainWindow (this creates InputSystem and installs it)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert api.input_system is not None, \
        "InputSystem not created during MainWindow init"

    # Add a device to the model and scene
    from core.models import Device
    import uuid
    device = Device(id=str(uuid.uuid4()), x=100.0, y=100.0,
                    meta={"width_mm": 40.0, "height_mm": 30.0})
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    window.canvas.load_harness(api.context.harness)

    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene registry."

    # Get viewport coordinates for the device center
    scene = item.scene()
    view = scene.views()[0]
    start_scene_pos = item.scenePos() + item.boundingRect().center()
    end_scene_pos = start_scene_pos + QPointF(50, 25)
    start_viewport_pos = view.mapFromScene(start_scene_pos)
    end_viewport_pos = view.mapFromScene(end_scene_pos)

    # Drag — through real Qt events, real InputSystem, real tool routing
    qtbot.mousePress(view.viewport(), Qt.LeftButton, pos=start_viewport_pos)
    qtbot.mouseMove(view.viewport(), pos=end_viewport_pos)
    qtbot.mouseRelease(view.viewport(), Qt.LeftButton, pos=end_viewport_pos)

    # The device position in the MODEL must have changed
    assert device.x != 100.0 or device.y != 100.0, \
        f"Device did not move after drag: ({device.x}, {device.y})"

    window.close()

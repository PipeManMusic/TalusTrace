import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device
from core.harness import DeviceList
from infra.context import Context
import uuid
from PySide6.QtCore import Qt, QPointF

def test_device_context_menu_delete_removes_device(qtbot):
    """
    Contract: Triggering 'Delete' from the device context menu must remove the device from the model and scene.
    """
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    api = APIManager(context=Context())
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)

    # Add a device
    device_id = str(uuid.uuid4())
    device = Device(id=device_id, x=100, y=100, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    api.dispatch("model_changed", {"action": "add", "item": device})

    # Load harness and get DeviceItem
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: api.get_scene_item(device_id) is not None, timeout=2000)
    device_item = api.get_scene_item(device_id)
    assert device_item is not None, "DeviceItem not found in scene registry."
    window._test_device_item = device_item

    # Simulate right-click to show context menu
    canvas = window.canvas
    scene_pos = device_item.scenePos()
    viewport_pos = canvas.mapFromScene(scene_pos)
    device_item.setSelected(True)
    shown_menu = {}
    def test_hook(data):
        menu = data['menu']
        shown_menu['menu'] = menu
        shown_menu['actions'] = [a.text() for a in menu.actions()]
        shown_menu['menu_type'] = data.get('menu_type')
    api.subscribe('context_menu', test_hook)
    qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=viewport_pos)
    qtbot.waitUntil(lambda: 'menu' in shown_menu, timeout=2000)

    # Find and trigger the 'Delete' action
    menu = shown_menu['menu']
    delete_action = None
    for action in menu.actions():
        if action.text().lower() in {"delete", "delete item"}:
            delete_action = action
            break
    assert delete_action is not None, f"Delete action not found in context menu: {[a.text() for a in menu.actions()]}"
    with qtbot.waitSignal(menu.triggered, timeout=2000, raising=False):
        delete_action.trigger()
    # Wait for device to be removed from model and scene
    def device_removed():
        return api.get_scene_item(device_id) is None and not any(d.id == device_id for d in api.context.harness.devices)
    try:
        qtbot.waitUntil(device_removed, timeout=2000)
    except Exception:
        # If waitUntil times out, device was not removed
        assert False, "Device was NOT removed from model and scene after context menu delete (TDD catch)."
    assert device_removed(), "Device was not removed from model and scene after context menu delete."
    window.close()

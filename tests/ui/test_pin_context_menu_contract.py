import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device, Pin
from core.harness import DeviceList
from infra.context import Context
import uuid
from PySide6.QtCore import Qt, QPointF

def test_pin_context_menu_shown_on_right_click(qtbot):
    """
    Contract: Right-clicking a pin must show a pin-specific context menu (not device/canvas menu or nothing).
    """
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    api = APIManager(context=Context())
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)

    # Add a device and pin
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=100, y=100, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin = Pin(id=pin_id, x=10, y=10, label="TestPin", side=0, device_id=device_id)
    device.pins.append(pin)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    api.dispatch("model_changed", {"action": "add", "item": device})
    api.dispatch("model_changed", {"action": "add", "item": pin})

    # Load harness and get PinItem
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: any(
        hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id
        for item in window.canvas.scene.items()
    ), timeout=2000)
    # Retrieve PinItem from scene to ensure it's alive
    pin_item = None
    for item in window.canvas.scene.items():
        if hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id:
            pin_item = item
            break
    assert pin_item is not None, "PinItem not found in scene."
    # Keep a strong reference to pin_item to prevent GC
    window._test_pin_item = pin_item

    # Install a test hook for context menu
    shown_menu = {}
    def test_hook(data):
        menu = data['menu']
        shown_menu['actions'] = [a.text() for a in menu.actions()]
        shown_menu['menu_type'] = data.get('menu_type')
    api.subscribe('context_menu', test_hook)

    # Simulate right-click (context menu) event at pin position
    canvas = window.canvas
    scene_pos = pin_item.scenePos()
    viewport_pos = canvas.mapFromScene(scene_pos)
    pin_item.setSelected(True)
    qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=viewport_pos)

    # Assert a menu was shown with expected pin-specific actions
    assert 'actions' in shown_menu, "No context menu was shown for pin."
    assert shown_menu.get('menu_type') == 'pin', f"Expected 'pin' menu, got '{shown_menu.get('menu_type')}'"
    expected_actions = {'Delete'}
    actual_actions = set(a for a in shown_menu['actions'] if a)
    missing = expected_actions - actual_actions
    assert not missing, f"Pin context menu missing actions: {missing}. Actual actions: {shown_menu['actions']}"
    window.close()

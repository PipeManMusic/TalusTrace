import pytest
from PySide6.QtCore import Qt, QPointF
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock
import os


def test_device_context_menu_shown_on_right_click(qtbot):
    """
    Contract: Right-clicking a device must show a device-specific context menu (not a canvas menu or nothing).
    """
    # Removed headless skip logic; always run the test
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = window.api
    # Install a test hook for context menu
    shown_menu = {}
    def test_hook(data):
        print(f"[DEBUG] test_hook called with data: {data}")
        menu = data['menu']
        pos = data.get('event').globalPos() if data.get('event') else None
        print(f'[TEST HOOK] Context menu shown with actions: {[a.text() for a in menu.actions()]} at pos: {pos}')
        shown_menu['actions'] = [a.text() for a in menu.actions()]
        shown_menu['pos'] = pos
    api.subscribe('context_menu', test_hook)
    try:
        # Add a device to the model and scene
        from core.models import Device
        import uuid
        device = Device(id=str(uuid.uuid4()), x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
        from core.harness import DeviceList
        with DeviceList.test_bypass():
            api.context.harness.devices.append(device)
        window.canvas.load_harness(api.context.harness)
        item = api.get_scene_item(device.id)
        assert item is not None, "DeviceItem not found in scene registry."
        # Simulate right-click (context menu) event at device position
        canvas = window.canvas
        # Use a point well inside the device bounding rect to guarantee hit
        from PySide6.QtCore import QPointF, QPoint
        # Use the device's actual scene position for the event
        scene_pos = item.scenePos()
        viewport_pos = canvas.mapFromScene(scene_pos)
        print(f'[TEST] scene_pos for event: {scene_pos}, viewport_pos: {viewport_pos}, device scenePos: {item.scenePos()}, boundingRect: {item.boundingRect()}')
        # Select the device first
        item.setSelected(True)
        # Simulate right-click mouse event at the device position
        print(f"[DEBUG] Simulating right-click at viewport_pos: {viewport_pos}")
        qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=viewport_pos)
        print(f"[DEBUG] shown_menu after click: {shown_menu}")
        # Assert a menu was shown with expected device-specific actions (by UUID)
        assert 'menu' in shown_menu, "No context menu was shown."
        menu = shown_menu['menu']
        # UUIDs from context_menu config: device.add_pin (command), rotate_cw (uuid), delete (uuid)
        expected_uuids = set([
            'device.add_pin',
            '4a88e033-860e-4b9b-9140-338b49c40e61',  # Rotate 90°
            'e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b'   # Delete
        ])
        def extract_uuid(data):
            if isinstance(data, dict):
                return data.get('uuid') or data.get('command')
            return data
        actual_uuids = set(extract_uuid(a.data()) for a in menu.actions() if a.data())
        missing = expected_uuids - actual_uuids
        assert not missing, f"Device context menu missing actions: {missing}. Actual UUIDs: {actual_uuids}"
    finally:
        if hasattr(api, '_test_context_menu_hook'):
            del api._test_context_menu_hook

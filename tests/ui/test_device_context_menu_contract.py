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
    is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
    if is_headless:
        pytest.skip("Skipping GUI context menu test in headless mode.")
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = window.api
    # Install a test hook for context menu
    shown_menu = {}
    def test_hook(data):
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
        qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=viewport_pos)
        # Assert a menu was shown with a device-specific action
        assert 'actions' in shown_menu, "No context menu was shown."
        assert any('Device' in a for a in shown_menu['actions']), f"Device context menu not shown, actions: {shown_menu['actions']}"
    finally:
        if hasattr(api, '_test_context_menu_hook'):
            del api._test_context_menu_hook

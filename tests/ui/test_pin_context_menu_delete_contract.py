
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device, Pin
from core.harness import DeviceList
from infra.context import Context
import uuid
from PySide6.QtCore import Qt, QPointF
from api.actions import register_device_command_actions
register_device_command_actions()

def test_pin_context_menu_delete_removes_pin(qtbot):
    """
    Contract: Triggering 'Delete' from the pin context menu must remove the pin from the device and scene.
    """
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    context = Context()
    api = APIManager(context=context)
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)
    # Subscribe canvas to model_changed events from the correct observer
    if hasattr(context, 'observer'):
        context.observer.subscribe('model_changed', window.canvas.on_model_changed)

    # Add a device and pin using APIManager contract methods
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=100, y=100, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin = Pin(id=pin_id, x=10, y=10, label="TestPin", side=0, device_id=device_id)
    # Use APIManager contract method to add device
    api.add_device(device)
    # Always reference the device from the harness after adding
    harness_device = next((d for d in api.context.harness.devices if getattr(d, 'id', None) == device_id), None)
    assert harness_device is not None, "Device not found in harness after add."
    # Add pin to the device using AddPinCommand only (do not append directly)
    from api.commands.device import AddPinCommand
    api.context.undo_stack.push(AddPinCommand(harness_device, pin, context=api.context))
    # Retrieve the pin instance from the harness device after command
    harness_pin = next((p for p in harness_device.pins if getattr(p, 'id', None) == pin_id), None)
    assert harness_pin is not None, "Pin not found in device after AddPinCommand."

    # Load harness and get PinItem
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: any(
        hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id
        for item in window.canvas.scene.items()
    ), timeout=2000)
    pin_item = None
    for item in window.canvas.scene.items():
        if hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id:
            pin_item = item
            break
    assert pin_item is not None, "PinItem not found in scene."
    window._test_pin_item = pin_item

    # Simulate right-click to show context menu
    canvas = window.canvas
    scene_pos = pin_item.scenePos()
    viewport_pos = canvas.mapFromScene(scene_pos)
    pin_item.setSelected(True)
    # Explicitly select the pin instance from the harness (ensures correct object identity)
    from core.selection import SelectionManager
    SelectionManager().select(harness_pin)
    shown_menu = {}
    def test_hook(data):
        menu = data['menu']
        shown_menu['menu'] = menu
        shown_menu['actions'] = [a.text() for a in menu.actions()]
        shown_menu['menu_type'] = data.get('menu_type')
    api.subscribe('context_menu', test_hook)
    qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=viewport_pos)
    qtbot.waitUntil(lambda: 'menu' in shown_menu, timeout=2000)

    # Find and trigger the 'Delete' action by UUID
    menu = shown_menu['menu']
    delete_uuid = 'e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b'
    delete_action = next((a for a in menu.actions() if a.data() == delete_uuid), None)
    assert delete_action is not None, f"Delete action (uuid={delete_uuid}) not found in context menu: {[a.data() for a in menu.actions()]}"
    with qtbot.waitSignal(menu.triggered, timeout=2000, raising=False):
        delete_action.trigger()
    # Wait for UI event loop to process removal
    qtbot.wait(100)
    # Wait for pin to be removed from device and scene
    def pin_removed():
        # Always check the device in the harness
        harness_device = next((d for d in api.context.harness.devices if getattr(d, 'id', None) == device_id), None)
        return api.get_scene_item(pin_id) is None and (harness_device is not None and not any(p.id == pin_id for p in harness_device.pins))
    try:
        qtbot.waitUntil(pin_removed, timeout=2000)
    except Exception:
        assert False, "Pin was NOT removed from device and scene after context menu delete (TDD catch)."
    assert pin_removed(), "Pin was not removed from device and scene after context menu delete."
    window.close()

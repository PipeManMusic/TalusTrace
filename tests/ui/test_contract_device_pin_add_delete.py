"""
Contract tests for event-to-core flow: device and pin add/delete actions.
Covers: event → selection → dispatch → API → infra → core → UI.
"""
import pytest
from PySide6.QtWidgets import QApplication
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.pin import Pin
from api.commands.device import AddPinCommand
from core.selection import SelectionManager
from ui.main_window import MainWindow

@pytest.mark.usefixtures("qtbot")
def test_contract_device_add_delete(qtbot):
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    context = Context()
    api = APIManager(context=context)
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)
    if hasattr(context, 'observer'):
        context.observer.subscribe('model_changed', window.canvas.on_model_changed)

    # Add device via contract
    import uuid
    device_id = str(uuid.uuid4())
    device = Device(id=device_id, x=10, y=10, meta={"width_mm": 20, "height_mm": 20}, pins=[])
    api.add_device(device)
    harness_device = next((d for d in api.context.harness.devices if d.id == device_id), None)
    assert harness_device is not None, "Device not found in harness after add."
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: any(
        hasattr(item, 'model') and getattr(item.model, 'id', None) == device_id
        for item in window.canvas.scene.items()
    ), timeout=2000)
    device_item = next((item for item in window.canvas.scene.items()
                       if hasattr(item, 'model') and getattr(item.model, 'id', None) == device_id), None)
    assert device_item is not None, "DeviceItem not found in scene."
    # Select device and delete via context menu
    SelectionManager().select(harness_device)
    shown_menu = {}
    def test_hook(data):
        shown_menu['menu'] = data['menu']
    api.subscribe('context_menu', test_hook)
    scene_pos = device_item.scenePos()
    viewport_pos = window.canvas.mapFromScene(scene_pos)
    device_item.setSelected(True)
    from PySide6.QtCore import Qt
    qtbot.mouseClick(window.canvas.viewport(), Qt.RightButton, pos=viewport_pos)
    qtbot.waitUntil(lambda: 'menu' in shown_menu, timeout=2000)
    menu = shown_menu['menu']
    delete_uuid = 'e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b'
    delete_action = next((a for a in menu.actions() if a.data() == delete_uuid), None)
    assert delete_action is not None, f"Delete action (uuid={delete_uuid}) not found in context menu: {[a.data() for a in menu.actions()]}"
    with qtbot.waitSignal(menu.triggered, timeout=2000, raising=False):
        delete_action.trigger()
    qtbot.wait(100)
    def device_removed():
        return api.get_scene_item(device_id) is None and not any(d.id == device_id for d in api.context.harness.devices)
    qtbot.waitUntil(device_removed, timeout=2000)
    assert device_removed(), "Device was NOT removed from harness and scene after context menu delete."

@pytest.mark.usefixtures("qtbot")
def test_contract_pin_add_delete(qtbot):
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    context = Context()
    api = APIManager(context=context)
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)
    if hasattr(context, 'observer'):
        context.observer.subscribe('model_changed', window.canvas.on_model_changed)

    # Add device and pin via contract
    import uuid
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=0, y=0, meta={"width_mm": 10, "height_mm": 10}, pins=[])
    pin = Pin(id=pin_id, x=1, y=1, label="Pin", side=0, device_id=device_id)
    api.add_device(device)
    harness_device = next((d for d in api.context.harness.devices if d.id == device_id), None)
    api.context.undo_stack.push(AddPinCommand(harness_device, pin, context=api.context))
    harness_pin = next((p for p in harness_device.pins if p.id == pin_id), None)
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: any(
        hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id
        for item in window.canvas.scene.items()
    ), timeout=2000)
    pin_item = next((item for item in window.canvas.scene.items()
                     if hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id), None)
    assert pin_item is not None, "PinItem not found in scene."
    # Select pin and delete via context menu
    SelectionManager().select(harness_pin)
    shown_menu = {}
    def test_hook(data):
        shown_menu['menu'] = data['menu']
    api.subscribe('context_menu', test_hook)
    scene_pos = pin_item.scenePos()
    viewport_pos = window.canvas.mapFromScene(scene_pos)
    pin_item.setSelected(True)
    from PySide6.QtCore import Qt
    qtbot.mouseClick(window.canvas.viewport(), Qt.RightButton, pos=viewport_pos)
    qtbot.waitUntil(lambda: 'menu' in shown_menu, timeout=2000)
    menu = shown_menu['menu']
    delete_uuid = 'e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b'
    delete_action = next((a for a in menu.actions() if a.data() == delete_uuid), None)
    assert delete_action is not None, f"Delete action (uuid={delete_uuid}) not found in context menu: {[a.data() for a in menu.actions()]}"
    with qtbot.waitSignal(menu.triggered, timeout=2000, raising=False):
        delete_action.trigger()
    qtbot.wait(100)
    def pin_removed():
        harness_device = next((d for d in api.context.harness.devices if d.id == device_id), None)
        return api.get_scene_item(pin_id) is None and (harness_device is not None and not any(p.id == pin_id for p in harness_device.pins))
    qtbot.waitUntil(pin_removed, timeout=2000)
    assert pin_removed(), "Pin was NOT removed from device and scene after context menu delete."

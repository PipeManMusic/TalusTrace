"""
Contract tests for verifying the flow of information from the UI to the infra layer in Talus Trace.
These tests ensure that UI actions (such as context menu deletes) propagate through the dispatcher,
command, and observer layers, resulting in correct model mutation and event dispatch.
"""
import pytest
from PySide6.QtWidgets import QApplication
from api.manager import APIManager
from core.selection import SelectionManager
from ui.main_window import MainWindow
from api.actions import actions_map

@pytest.mark.usefixtures("qtbot")
def test_ui_to_infra_pin_delete_contract(qtbot, populated_api):
    """
    Contract: Deleting a pin via the UI context menu must propagate through the dispatcher,
    command, and observer layers, resulting in the pin being removed from the device and scene.
    """
    app = QApplication.instance() or QApplication([])
    api, harness_device, harness_pin, device_id, pin_id = populated_api
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)
    context = api.context
    if hasattr(context, 'observer'):
        context.observer.subscribe('model_changed', window.canvas.on_model_changed)
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: any(
        hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id
        for item in window.canvas.scene.items()
    ), timeout=2000)
    pin_item = next((item for item in window.canvas.scene.items()
                     if hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id), None)
    assert pin_item is not None, "PinItem not found in scene."
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
    target_cmd = "edit.delete"
    target_uuid = actions_map.get(target_cmd, {}).get("uuid")
    delete_action = next(
        (
            a
            for a in menu.actions()
            if a.data() == target_cmd
            or a.data() == target_uuid
            or (isinstance(a.data(), dict) and (a.data().get("uuid") == target_uuid or a.data().get("action") == target_cmd))
        ),
        None,
    )
    assert delete_action is not None, f"Delete action (cmd={target_cmd}, uuid={target_uuid}) not found in context menu: {[a.data() for a in menu.actions()]}"
    with qtbot.waitSignal(menu.triggered, timeout=2000, raising=False):
        delete_action.trigger()
    def pin_removed():
        harness_device_local = next((d for d in api.context.harness.devices if d.id == device_id), None)
        return api.get_scene_item(pin_id) is None and (harness_device_local is not None and not any(p.id == pin_id for p in harness_device_local.pins))
    qtbot.waitUntil(pin_removed, timeout=2000)
    assert pin_removed(), "Pin was NOT removed from device and scene after context menu delete."

# Additional contract tests for device delete, add, and update flows can be added similarly.

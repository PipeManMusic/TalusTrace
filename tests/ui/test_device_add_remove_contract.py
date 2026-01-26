import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from ui.canvas import HarnessCanvas
from core.device import Device
from api.manager import APIManager
from infra.context import Context

@pytest.fixture
def canvas_and_api(qtbot: QtBot):
    APIManager.reset()
    context = Context()
    api = APIManager.get_instance(context=context)
    # Ensure dispatcher actions are registered
    from api.actions import register_device_command_actions
    register_device_command_actions()
    canvas = HarnessCanvas()
    qtbot.addWidget(canvas)
    canvas.show()
    api.main_window = type("FakeMainWindow", (), {"canvas": canvas})()
    # Subscribe canvas to model_changed events from the correct observer
    if hasattr(context, 'observer'):
        context.observer.subscribe('model_changed', canvas.on_model_changed)
    return canvas, api, qtbot

def test_device_add_remove_contract(canvas_and_api):
    canvas, api, qtbot = canvas_and_api
    import uuid
    device = Device(id=str(uuid.uuid4()), x=10, y=10)
    # Add device via dispatcher
    # Use the same context instance for dispatcher calls to ensure observer consistency
    context = api.context
    context.device = device
    from infra.logging import infra_log
    infra_log(f"[TEST] Dispatching 'edit.add' for device id={device.id}", level="debug")
    api.dispatch("edit.add", context)
    qtbot.wait(200)  # Let event loop process
    infra_log(f"[TEST] Scene items after add: {[getattr(item, 'model', None) for item in canvas.scene.items()]}", level="debug")
    # Assert device is in scene
    items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
    infra_log(f"[TEST] DeviceItem(s) found for device id={device.id}: {items}", level="debug")
    assert items, "DeviceItem not added to scene."
    # Remove device via dispatcher (contract-compliant)
    # Use the same context instance for delete as well
    context.device = device
    from infra.logging import infra_log
    infra_log(f"[TEST] Dispatching 'edit.delete' for device id={device.id}", level="debug")
    api.dispatch("edit.delete", context)
    qtbot.wait(200)
    # Assert device is removed from scene
    items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
    infra_log(f"[TEST] DeviceItem(s) after delete for device id={device.id}: {items}", level="debug")
    assert not items, "DeviceItem still present in scene after removal."

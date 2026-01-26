"""
Test that PinItem is registered in the APIManager scene registry when a pin is added, and is updated on model change.
"""
import pytest
from PySide6.QtWidgets import QApplication
from api.manager import APIManager
from infra.context import Context
from core.device import Device, Pin
from ui.main_window import MainWindow
from ui.canvas import HarnessCanvas

def test_pinitem_scene_registry_and_update(qtbot):
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
    import uuid
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin = Pin(id=pin_id, x=5, y=5, label="TestPin", side=0, device_id=device_id)
    api.add_device(device)
    from api.commands.device import AddPinCommand
    api.context.undo_stack.push(AddPinCommand(device, pin, context=api.context))

    # PinItem should be registered
    pin_item = api.get_scene_item(pin_id)
    assert pin_item is not None, "PinItem was not registered in the scene registry"
    assert abs(pin_item.x() - 5) < 0.01 and abs(pin_item.y() - 5) < 0.01, "PinItem initial position incorrect"

    # Update pin position
    pin.x = 77
    pin.y = 88
    api.dispatch("model_changed", {"action": "update", "item": pin})
    qtbot.waitUntil(lambda: abs(pin_item.x() - 77) < 0.01 and abs(pin_item.y() - 88) < 0.01, timeout=3000)

"""
Test that adding a Pin to the model results in a PinItem (ellipse) in the scene, not a DeviceItem (rectangle).
Fails if a Pin is rendered as a DeviceItem or not as a PinItem.
"""
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device, Pin
from core.harness import DeviceList
from infra.context import Context
import uuid

def find_scene_item_of_type(scene, item_type):
    return [item for item in scene.items() if isinstance(item, item_type)]

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

def test_pin_add_creates_pinitem_not_deviceitem(main_window, api_manager):
    from ui.items.pin import PinItem
    from ui.items.device import DeviceItem
    # Add a device
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    with DeviceList.test_bypass():
        api_manager.context.harness.devices.append(device)
    # Dispatch model_changed for device so DeviceItem is created
    main_window.api.dispatch("model_changed", {"action": "add", "item": device})
    # Add a pin and dispatch model_changed
    pin = Pin(id=pin_id, x=5, y=5, label="TestPin", side=0, device_id=device_id)
    device.pins.append(pin)
    main_window.api.dispatch("model_changed", {"action": "add", "item": pin})
    # Find PinItem and DeviceItem in the scene
    canvas = main_window.canvas
    pin_items = find_scene_item_of_type(canvas.scene, PinItem)
    device_items = find_scene_item_of_type(canvas.scene, DeviceItem)
    # PinItem for the pin must exist
    assert any(getattr(item, "model", None) == pin for item in pin_items), "Pin was not rendered as a PinItem in the scene"
    # No DeviceItem should have the pin as its model
    assert not any(getattr(item, "model", None) == pin for item in device_items), "Pin was incorrectly rendered as a DeviceItem"

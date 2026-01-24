"""
Test that creating a pin on a device results in the pin being displayed in the UI.
Fails if the pin is not visible after creation.
"""
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device, Pin
from infra.context import Context
import uuid

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

def test_pin_displayed_after_creation(main_window, api_manager):
    # Create a device and add it to the context
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api_manager.context.harness.devices.append(device)
    # Simulate UI selection of the device
    main_window.api.dispatch("selection_changed", {"selection": [device]})
    # Add a pin to the device
    pin = Pin(id=pin_id, x=5, y=5, label="TestPin", side=0)
    device.pins.append(pin)
    # Simulate model change event
    main_window.api.dispatch("model_changed", {"item": device})
    # The pin should now be visible in the UI (PropertiesPanel or canvas)
    # Check PropertiesPanel for pin fields
    panel = getattr(main_window, "properties_panel", None)
    assert panel is not None, "PropertiesPanel not found on MainWindow"
    found = False
    for i in range(panel.form.count()):
        row = panel.form.itemAt(i)
        if row and row.widget() and hasattr(row.widget(), 'text'):
            if pin_id in row.widget().text() or "Pin" in row.widget().text():
                found = True
                break
    assert found, "Pin not displayed in PropertiesPanel after creation"

import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device, Pin
from core.harness import DeviceList
from infra.context import Context
import uuid
from PySide6.QtWidgets import QLabel, QFormLayout

def test_pin_property_panel_updates_canvas(qtbot):
    """
    Contract: Changing pin x/y in the properties panel updates the pin's position in the canvas via the API and event system.
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
    device = Device(id=device_id, x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin = Pin(id=pin_id, x=5, y=5, label="TestPin", side=0, device_id=device_id)
    device.pins.append(pin)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    # Dispatch model_changed for device and pin
    api.dispatch("model_changed", {"action": "add", "item": device})
    api.dispatch("model_changed", {"action": "add", "item": pin})

    # Select the pin in the properties panel
    api.dispatch("selection_changed", {"selection": [pin]})
    panel = window.properties_panel
    qtbot.waitUntil(lambda: hasattr(panel, 'form'), timeout=3000)

    # Find the Rel X and Rel Y QLineEdit fields
    rel_x_edit = None
    rel_y_edit = None
    for i in range(panel.form.rowCount()):
        label_item = panel.form.itemAt(i, QFormLayout.LabelRole)
        if label_item is None:
            continue
        label = label_item.widget()
        if isinstance(label, QLabel):
            if label.text() == "Rel X":
                field_item = panel.form.itemAt(i, QFormLayout.FieldRole)
                if field_item is not None:
                    rel_x_edit = field_item.widget()
            elif label.text() == "Rel Y":
                field_item = panel.form.itemAt(i, QFormLayout.FieldRole)
                if field_item is not None:
                    rel_y_edit = field_item.widget()
    assert rel_x_edit is not None and rel_y_edit is not None, "Pin geometry fields not found"

    # Change x/y in the panel
    rel_x_edit.setText("42")
    rel_x_edit.editingFinished.emit()
    rel_y_edit.setText("99")
    rel_y_edit.editingFinished.emit()

    # Wait for canvas to update
    canvas = window.canvas
    def pin_item_at_expected():
        for item in canvas.scene.items():
            if hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id:
                return abs(item.x() - 42) < 0.01 and abs(item.y() - 99) < 0.01
        return False
    qtbot.waitUntil(pin_item_at_expected, timeout=3000)
    assert pin_item_at_expected(), "PinItem position did not update in canvas after property panel change"
    window.close()

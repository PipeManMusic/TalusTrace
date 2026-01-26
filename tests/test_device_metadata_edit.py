"""
Test that device metadata fields (other than label) are editable and persist via the API, and that undo/redo works for meta fields.
"""
import pytest
from PySide6.QtWidgets import QApplication, QFormLayout
from api.manager import APIManager
from core.device import Device
from core.harness import DeviceList
from infra.context import Context
from ui.main_window import MainWindow

def test_device_metadata_edit_and_undo(qtbot):
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    api = APIManager(context=Context())
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)

    # Add a device with a meta field
    import uuid
    device_id = str(uuid.uuid4())
    device = Device(id=device_id, x=0, y=0, meta={"foo": "bar"}, label="TestDevice")
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    api.dispatch("model_changed", {"action": "add", "item": device})

    # Select the device in the properties panel
    api.dispatch("selection_changed", {"selection": [device]})
    panel = window.properties_panel
    qtbot.waitUntil(lambda: hasattr(panel, 'form'), timeout=3000)

    # Find the meta field QLineEdit (label 'foo')
    meta_edit = None
    for i in range(panel.form.rowCount()):
        label_item = panel.form.itemAt(i, QFormLayout.LabelRole)
        if label_item is None:
            continue
        label = label_item.widget()
        if label and label.text() == "foo":
            field_item = panel.form.itemAt(i, QFormLayout.FieldRole)
            if field_item is not None:
                meta_edit = field_item.widget()
                break
    assert meta_edit is not None, "Meta field 'foo' not found in properties panel"

    # Change the meta field value
    meta_edit.setText("baz")
    meta_edit.editingFinished.emit()
    qtbot.waitUntil(lambda: device.meta.get("foo") == "baz", timeout=2000)
    assert device.meta["foo"] == "baz", "Meta field did not update via API"

    # Undo the change
    api.context.undo_stack.undo()
    qtbot.waitUntil(lambda: device.meta.get("foo") == "bar", timeout=2000)
    assert device.meta["foo"] == "bar", "Meta field did not revert on undo"

    # Redo the change
    api.context.undo_stack.redo()
    qtbot.waitUntil(lambda: device.meta.get("foo") == "baz", timeout=2000)
    assert device.meta["foo"] == "baz", "Meta field did not re-apply on redo"

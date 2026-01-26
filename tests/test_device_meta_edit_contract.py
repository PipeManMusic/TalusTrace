import pytest
from PySide6.QtWidgets import QApplication, QFormLayout, QLineEdit, QComboBox
from api.manager import APIManager
from core.device import Device
from infra.context import Context
from ui.main_window import MainWindow
from core.metadata import MetadataManager

@pytest.mark.parametrize("meta_key, initial, updated", [
    ("width_mm", 40.0, 55.0),
    ("height_mm", 30.0, 45.0),
    ("manufacturer", "Generic", "TestCo"),
    ("sku", "", "ABC123"),
])
def test_device_meta_edit_and_undo_redo(qtbot, meta_key, initial, updated):
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    api = APIManager(context=Context())
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)

    # Reset MetadataManager singleton to ensure schema is used
    from core.metadata import MetadataManager
    MetadataManager._instance = None
    meta_mgr = MetadataManager.get_instance()
    meta_mgr.schemas = {
        "generic": {
            "label": "Generic Device",
            "icon": "square",
            "fields": {
                "width_mm": {"type": "float", "default": 40.0, "label": "Width (mm)", "min": 5.0, "max": 500.0},
                "height_mm": {"type": "float", "default": 30.0, "label": "Height (mm)"},
                "manufacturer": {"type": "string", "default": "Generic", "label": "Manufacturer"},
                "sku": {"type": "string", "default": "", "label": "Part Number"},
            }
        }
    }

    # Add a device with meta fields
    import uuid
    device_id = str(uuid.uuid4())
    meta = {"width_mm": 40.0, "height_mm": 30.0, "manufacturer": "Generic", "sku": "", "_type": "generic"}
    device = Device(id=device_id, x=0, y=0, meta=meta.copy(), label="TestDevice")
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    api.dispatch("model_changed", {"action": "add", "item": device})

    # Select the device in the properties panel
    api.dispatch("selection_changed", {"selection": [device]})
    panel = window.properties_panel
    qtbot.waitUntil(lambda: hasattr(panel, 'form'), timeout=3000)

    # Map meta_key to schema label
    key_to_label = {
        "width_mm": "Width (mm)",
        "height_mm": "Height (mm)",
        "manufacturer": "Manufacturer",
        "sku": "Part Number",
    }
    field_label = key_to_label[meta_key]
    # Find the meta field editor by label
    meta_edit = None
    for i in range(panel.form.rowCount()):
        label_item = panel.form.itemAt(i, QFormLayout.LabelRole)
        if label_item is None:
            continue
        label = label_item.widget()
        if label and label.text() == field_label:
            field_item = panel.form.itemAt(i, QFormLayout.FieldRole)
            if field_item is not None:
                widget = field_item.widget()
                meta_edit = widget
                break
    assert meta_edit is not None, f"Meta field '{meta_key}' (label '{field_label}') not found in properties panel"

    # Edit the meta field
    if isinstance(meta_edit, QLineEdit):
        meta_edit.setText(str(updated))
        meta_edit.editingFinished.emit()
    elif isinstance(meta_edit, QComboBox):
        meta_edit.setCurrentText(str(updated))
    else:
        raise AssertionError(f"Unknown widget type for meta field '{meta_key}'")

    # Wait for model to update
    qtbot.waitUntil(lambda: str(device.meta[meta_key]) == str(updated), timeout=2000)
    assert str(device.meta[meta_key]) == str(updated), f"Meta field '{meta_key}' did not update via API"
    # Enforce type correctness for float fields
    if meta_key in ("width_mm", "height_mm"):
        assert isinstance(device.meta[meta_key], float), f"Meta field '{meta_key}' is not float after edit: {type(device.meta[meta_key])}"

    # Undo the change
    api.context.undo_stack.undo()
    qtbot.waitUntil(lambda: str(device.meta[meta_key]) == str(initial), timeout=2000)
    assert str(device.meta[meta_key]) == str(initial), f"Meta field '{meta_key}' did not revert on undo"
    if meta_key in ("width_mm", "height_mm"):
        assert isinstance(device.meta[meta_key], float), f"Meta field '{meta_key}' is not float after undo: {type(device.meta[meta_key])}"

    # Redo the change
    api.context.undo_stack.redo()
    qtbot.waitUntil(lambda: str(device.meta[meta_key]) == str(updated), timeout=2000)
    assert str(device.meta[meta_key]) == str(updated), f"Meta field '{meta_key}' did not reapply on redo"
    if meta_key in ("width_mm", "height_mm"):
        assert isinstance(device.meta[meta_key], float), f"Meta field '{meta_key}' is not float after redo: {type(device.meta[meta_key])}"

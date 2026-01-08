import pytest
from PySide6.QtWidgets import QApplication
from core.device import Device
from core.selection import SelectionManager
# Target Implementation: ui/panels/properties.py
from ui.panels.properties import PropertyPanel

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_property_panel_updates_model(qapp):
    # 1. Setup
    dev = Device(id="OLD_ID")
    global _device_registry
    try:
        _device_registry
    except NameError:
        _device_registry = {}
    _device_registry[dev.id] = dev
    SelectionManager().set_selection([dev])
    panel = PropertyPanel()
    
    # 2. Verify Panel loaded data
    assert panel.id_field.text() == "OLD_ID"
    
    # 3. Edit Data
    panel.id_field.setText("NEW_ID")
    panel.apply_changes() # Should trigger RenameDeviceCommand
    
    # 4. Verify Model Update
    # After id change, look up by new id in registry
    # Fetch the device from the registry after id change
    updated_dev = _device_registry.get("NEW_ID")
    assert updated_dev is not None, "Device with NEW_ID not found in registry after apply_changes()"
    assert updated_dev.id == "NEW_ID"
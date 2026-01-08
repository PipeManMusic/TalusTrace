import pytest
from PySide6.QtWidgets import QApplication
from core.device import Device
from core.selection import SelectionManager
# Target Implementation: ui/panels/properties.py
from ui.panels.properties import PropertyPanel, device_registry

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_property_panel_updates_model(qapp):
    # 1. Setup
    dev = Device(id="OLD_ID")
    
    # CRITICAL FIX: Populate the shared module-level registry
    device_registry.clear()
    device_registry[dev.id] = dev
    
    SelectionManager().set_selection([dev])
    
    # Debug verification
    print(f"TEST SETUP: Registry has {device_registry.keys()}")
    
    panel = PropertyPanel()
    
    # 2. Verify Panel loaded data
    assert panel.id_field.text() == "OLD_ID"
    
    # 3. Edit Data
    panel.id_field.setText("NEW_ID")
    panel.apply_changes() 
    
    # 4. Verify Model Update
    # The device instance itself should be mutated
    assert dev.id == "NEW_ID"
    
    # The registry should also reflect the new key
    updated_dev = device_registry.get("NEW_ID")
    assert updated_dev is not None
    assert updated_dev.id == "NEW_ID"
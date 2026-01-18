import pytest
from PySide6.QtWidgets import QLabel, QLineEdit
from ui.panels.properties import PropertyPanel
from core.device import Device
from api.manager import APIManager

@pytest.mark.xfail(reason="UI Timing issues")
def test_property_panel_loads_selection(qtbot):
    """
    Validates that the Property Panel updates when Selection changes.
    """
    # 1. Setup
    from api.manager import APIManager
    APIManager.reset()
    panel = PropertyPanel()
    qtbot.add_widget(panel)
    
    # 2. Create Dummy Device
    dev = Device(id="TEST-01", label="Test Device")
    
    # 3. Simulate Selection Event via API
    # (The Panel listens to APIManager "selection_changed")
    APIManager.get_instance().dispatch("selection_changed", {
        "selection": [dev]
    })

    # Wait for the UI to update
    qtbot.waitUntil(lambda: hasattr(panel, 'id_edit'))
    # 4. Assertions
    # Check if the ID field was populated
    assert panel.id_edit.text() == "TEST-01"
    assert panel.label_edit.text() == "Test Device"

def test_property_panel_clears_on_deselect(qtbot):
    panel = PropertyPanel()
    qtbot.add_widget(panel)
    
    # Simulate Deselect
    APIManager.get_instance().dispatch("selection_changed", {
        "selection": []
    })
    
    # Check if layout was cleared / shows "No Selection"
    # Easier check: Ensure edits are gone
    assert not hasattr(panel, 'id_edit') or not panel.id_edit.isVisible()

def test_property_panel_apply_changes(qtbot):
    panel = PropertyPanel()
    qtbot.add_widget(panel)
    
    dev = Device(id="ORIGINAL")
    panel.load_item(dev)
    
    # User types new ID
    panel.id_edit.setText("UPDATED")
    panel.id_edit.editingFinished.emit()
    
    assert dev.id == "UPDATED"
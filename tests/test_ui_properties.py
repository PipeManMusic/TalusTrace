import pytest
from PySide6.QtWidgets import QLabel, QLineEdit
# FIXED: Updated import to match the renamed class
from ui.panels.properties import PropertiesPanel
from core.device import Device
from api.manager import APIManager

def test_property_panel_loads_selection(qtbot):
    """
    Validates that the Property Panel updates when Selection changes.
    """
    # 1. Setup & Reset API
    APIManager._instance = None 
    api = APIManager.get_instance()
    
    # FIXED: Updated class usage
    panel = PropertiesPanel()
    qtbot.add_widget(panel)
    panel.show() 
    
    # 2. Create Dummy Device
    dev = Device(id="TEST-01", label="Test Device")
    
    # 3. Simulate Selection Event via API
    api.dispatch("selection_changed", {
        "selection": [dev]
    })

    # 4. Wait for UI Update
    qtbot.waitUntil(lambda: hasattr(panel, 'id_edit') and panel.id_edit.text() == "TEST-01", timeout=3000)
    
    # 5. Assertions
    assert panel.id_edit.text() == "TEST-01"
    assert panel.label_edit.text() == "Test Device"

def test_property_panel_clears_on_deselect(qtbot):
    APIManager._instance = None 
    api = APIManager.get_instance()
    
    panel = PropertiesPanel()
    qtbot.add_widget(panel)
    panel.show()
    
    api.dispatch("selection_changed", {
        "selection": []
    })
    
    def check_cleared():
        return not hasattr(panel, 'id_edit') or not panel.id_edit.isVisible()
        
    qtbot.waitUntil(check_cleared, timeout=3000)
    
    assert check_cleared()

def test_property_panel_apply_changes(qtbot):
    APIManager._instance = None 
    
    panel = PropertiesPanel()
    qtbot.add_widget(panel)
    panel.show()
    
    dev = Device(id="ORIGINAL")
    panel.load_item(dev) 
    
    assert hasattr(panel, 'id_edit')
    
    panel.id_edit.setText("UPDATED")
    panel.id_edit.editingFinished.emit()
    
    assert dev.id == "UPDATED"
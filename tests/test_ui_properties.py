import pytest
from PySide6.QtWidgets import QLabel, QLineEdit
from ui.panels.properties import PropertyPanel
from core.device import Device
from api.manager import APIManager

def test_property_panel_loads_selection(qtbot):
    """
    Validates that the Property Panel updates when Selection changes.
    """
    # 1. Setup & Reset API
    # Force a clean singleton instance to ensure event subscriptions work
    APIManager._instance = None 
    api = APIManager.get_instance()
    
    panel = PropertyPanel()
    qtbot.add_widget(panel)
    panel.show() # Critical: Ensure widget is visible/active for layout updates
    
    # 2. Create Dummy Device
    dev = Device(id="TEST-01", label="Test Device")
    
    # 3. Simulate Selection Event via API
    # The Panel listens to APIManager "selection_changed"
    api.dispatch("selection_changed", {
        "selection": [dev]
    })

    # 4. Wait for UI Update
    # Wait until the dynamic 'id_edit' field is created and populated
    qtbot.waitUntil(lambda: hasattr(panel, 'id_edit') and panel.id_edit.text() == "TEST-01", timeout=3000)
    
    # 5. Assertions
    assert panel.id_edit.text() == "TEST-01"
    assert panel.label_edit.text() == "Test Device"

def test_property_panel_clears_on_deselect(qtbot):
    # Reset API for this test too
    APIManager._instance = None 
    api = APIManager.get_instance()
    
    panel = PropertyPanel()
    qtbot.add_widget(panel)
    panel.show()
    
    # Setup initial state (implicitly) or just fire deselect
    api.dispatch("selection_changed", {
        "selection": []
    })
    
    # Check if layout was cleared.
    # We wait until id_edit is gone or hidden
    def check_cleared():
        return not hasattr(panel, 'id_edit') or not panel.id_edit.isVisible()
        
    qtbot.waitUntil(check_cleared, timeout=3000)
    
    assert check_cleared()

def test_property_panel_apply_changes(qtbot):
    # Reset API
    APIManager._instance = None 
    
    panel = PropertyPanel()
    qtbot.add_widget(panel)
    panel.show()
    
    dev = Device(id="ORIGINAL")
    panel.load_item(dev) # Direct load for this unit test
    
    # User types new ID
    # We must ensure id_edit exists first (load_item should create it)
    assert hasattr(panel, 'id_edit')
    
    panel.id_edit.setText("UPDATED")
    panel.id_edit.editingFinished.emit()
    
    assert dev.id == "UPDATED"
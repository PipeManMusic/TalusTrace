import pytest
from PySide6.QtWidgets import QLineEdit
from api.manager import APIManager
from core.device import Device
from ui.panels.properties import PropertiesPanel

def test_device_id_edit_bypasses_undo_stack(qtbot):
    """
    Compliance Audit Test: PH5-EDIT.2 (The "Rogue Edit" Violation).
    
    Current Behavior (BROKEN):
    1. PropertiesPanel updates device.id directly in the lambda.
    2. No Command is pushed to the stack.
    3. Calling undo() does nothing.
    
    Expected Behavior (COMPLIANT):
    1. PropertiesPanel uses UpdatePropertyCommand.
    2. Undo() reverts the ID to its original value.
    """
    # 1. Setup: Reset API
    APIManager.reset()
    api = APIManager.get_instance()
    
    # Create a panel and widget
    panel = PropertiesPanel()
    qtbot.addWidget(panel)
    panel.show()
    
    # 2. Create a Device
    original_id = "DEV_001"
    device = Device(id=original_id, x=0, y=0)
    api.context.harness.devices.append(device)
    
    # 3. Load into Panel
    panel.load_item(device)
    
    # Verify the UI field exists
    assert hasattr(panel, 'id_edit'), "Panel failed to render ID field"
    assert isinstance(panel.id_edit, QLineEdit)
    assert panel.id_edit.text() == original_id
    
    # 4. Action: User changes ID
    new_id = "DEV_EDITED"
    panel.id_edit.setText(new_id)
    panel.id_edit.editingFinished.emit() # Trigger the 'update_id' callback
    
    # Verify the model updated (Real-time update is happening)
    assert device.id == new_id, "Model should have updated to new ID"
    
    # 5. Check Undo Stack (The Trap)
    # If a command was used, the stack index should be > 0 (or we check canUndo)
    # Note: If no command was pushed, undo() is a no-op.
    
    api.context.undo_stack.undo()
    
    # 6. Critical Assertion
    # This will FAIL if the code is violating the Command Pipeline.
    # The ID will still be "DEV_EDITED" because the change wasn't recorded.
    assert device.id == original_id, \
        f"VIOLATION: Undo failed! Device ID remained '{device.id}' instead of reverting to '{original_id}'. " \
        "This proves PropertiesPanel is mutating state directly."

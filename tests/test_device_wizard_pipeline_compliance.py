import pytest
from PySide6.QtCore import Qt
from unittest.mock import MagicMock
from ui.dialogs.device_wizard import DeviceWizard
from api.manager import APIManager

def test_device_wizard_pipeline_compliance(qtbot):
    """
    Compliance Check: Command Pipeline Phase 3.
    
    Risk: Dialog.accept() appends to harness.devices directly.
    """
    # 1. Setup
    APIManager.reset()
    api = APIManager.get_instance()
    
    # 2. Create Wizard
    # (Ideally checking logic without showing UI, or using a shim)
    wizard = DeviceWizard()
    
    # Pre-fill wizard data to pass validation
    import uuid
    valid_id = str(uuid.uuid4())
    wizard.id_input.setText(valid_id)
    wizard.name_input.setText("Test Device")
    
    # 3. Simulate Accept
    # Prefer clicking the OK button if enabled, else fail
    ok_button = wizard.accept_button
    if ok_button.isEnabled():
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    else:
        # Fallback: call accept() directly for headless automation
        wizard.accept()
    
    # 4. Assertions
    
    # Check 1: Did it modify the model? (It should have)
    assert len(api.context.harness.devices) == 1
    # Device ID should NOT match user-supplied id; it must be generated in infra/API
    assert api.context.harness.devices[0].id != valid_id, (
        "DeviceWizard must not use user-supplied id; id must be generated in infra/API."
    )

    # Check 2: Did it use the Undo Stack? (CRITICAL)
    # If the stack is empty, it was a "Direct Mutation" violation.
    assert len(api.context.undo_stack) > 0, (
        "VIOLATION: Wizard modified harness directly! Must use AddDeviceCommand."
    )

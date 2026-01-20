import pytest
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
    wizard.id_input.setText("NEW_DEV")
    wizard.name_input.setText("Test Device")
    
    # 3. Simulate Accept
    # We call the logic bound to the 'OK' button directly
    wizard.accept()
    
    # 4. Assertions
    
    # Check 1: Did it modify the model? (It should have)
    assert len(api.context.harness.devices) == 1
    assert api.context.harness.devices[0].id == "NEW_DEV"
    
    # Check 2: Did it use the Undo Stack? (CRITICAL)
    # If the stack is empty, it was a "Direct Mutation" violation.
    assert len(api.context.undo_stack) > 0, \
        "VIOLATION: Wizard modified harness directly! Must use AddDeviceCommand."

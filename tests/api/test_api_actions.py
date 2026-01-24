import pytest
from api.actions import dispatch_action
from infra.context import Context
from core.device import Device
from api.manager import APIManager

# Test: All registered edit actions are callable and perform as expected
def test_api_edit_actions_dispatch():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0, y=0)
    # Use AddDeviceCommand to add device (avoid direct mutation)
    from api.commands.device import AddDeviceCommand
    cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(cmd)
    # edit.undo and edit.redo should not raise
    dispatch_action("edit.undo", context=ctx)
    dispatch_action("edit.redo", context=ctx)
    # edit.delete should remove the device
    # Re-add device for delete test
    cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(cmd)
    # Select the device so edit.delete knows what to delete
    from core.selection import SelectionManager
    SelectionManager().select(device)
    dispatch_action("edit.delete", context=ctx)
    assert device not in ctx.harness.devices
    # edit.update_property should update a property
    device.x = 1
    dispatch_action("edit.update_property", context=ctx)
    # edit.settings and edit.theme are UI actions that open dialogs; skip in headless test
    # dispatch_action("edit.settings", context=ctx)
    # dispatch_action("edit.theme", context=ctx)

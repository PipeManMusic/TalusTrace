
import pytest
import uuid
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.wire import Wire
from api.commands.edit import UpdatePropertyCommand, DeleteItemsCommand, RotateItemsCommand

# Test: UpdatePropertyCommand (edit property, undo/redo)
def test_api_update_property_command():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    device = Device(id=str(uuid.uuid4()), x=10, y=20, meta={"foo": "bar"})
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device, context=ctx))
    # Update x property
    cmd = UpdatePropertyCommand(device, "x", 99)
    ctx.undo_stack.push(cmd)
    assert device.x == 99
    # Undo
    ctx.undo_stack.undo()
    assert device.x == 10
    # Redo
    ctx.undo_stack.redo()
    assert device.x == 99

# Test: DeleteItemsCommand (delete device, undo/redo)
def test_api_delete_items_command():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    device = Device(id=str(uuid.uuid4()), x=0, y=0)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device, context=ctx))
    cmd = DeleteItemsCommand([device], [])
    ctx.undo_stack.push(cmd)
    assert device not in ctx.harness.devices
    # Undo
    ctx.undo_stack.undo()
    assert device in ctx.harness.devices
    # Redo
    ctx.undo_stack.redo()
    assert device not in ctx.harness.devices

# Test: RotateItemsCommand (rotate device, undo/redo)
def test_api_rotate_items_command():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    device = Device(id=str(uuid.uuid4()), x=0, y=0, rotation=0)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device, context=ctx))
    cmd = RotateItemsCommand([device], 90)
    ctx.undo_stack.push(cmd)
    assert getattr(device, "rotation", None) == 90
    # Undo
    ctx.undo_stack.undo()
    assert getattr(device, "rotation", None) == 0
    # Redo
    ctx.undo_stack.redo()
    assert getattr(device, "rotation", None) == 90

# Test: UpdatePropertyCommand with invalid property
def test_api_update_property_invalid():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    device = Device(id=str(uuid.uuid4()), x=0, y=0)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device, context=ctx))
    cmd = UpdatePropertyCommand(device, "nonexistent", 123)
    ctx.undo_stack.push(cmd)
    # No error is expected; setting a nonexistent attribute just adds it

# Test: DeleteItemsCommand with non-existent device
def test_api_delete_items_nonexistent():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    device = Device(id=str(uuid.uuid4()), x=0, y=0)
    # Not added to harness
    cmd = DeleteItemsCommand([device], [])
    ctx.undo_stack.push(cmd)
    # Should not raise, just be a no-op
    assert device not in ctx.harness.devices

# Test: RotateItemsCommand with empty list
def test_api_rotate_items_empty():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    cmd = RotateItemsCommand([], 45)
    ctx.undo_stack.push(cmd)
    # Should not raise

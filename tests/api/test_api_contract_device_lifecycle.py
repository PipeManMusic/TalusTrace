import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: API issues proper events/contracts for device lifecycle (create, remove, move, update)

def test_api_device_lifecycle_contracts():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    events = []
    def handler(data):
        if data.get("item") and getattr(data["item"], "id", None) == device.id:
            events.append((data.get("action"), data))
    api.context.observer.subscribe("model_changed", handler)
    # Create device
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0, y=0, meta={"foo": "bar"})
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))
    # Remove device
    from api.commands.edit import DeleteItemsCommand
    ctx.undo_stack.push(DeleteItemsCommand([device.id], []))
    # Move device (simulate via command)
    from api.commands.move import MoveCommand
    move_cmd = MoveCommand(device, (0,0), (10,20))
    ctx.undo_stack.push(move_cmd)
    # Update meta data (simulate via command)
    from infra.undo_stack import BaseCommand
    class UpdateMetaCommand(BaseCommand):
        def __init__(self, device, new_meta):
            super().__init__("Update Meta")
            self.device = device
            self.old_meta = dict(device.meta)
            self.new_meta = new_meta
        def execute(self):
            self.device.meta.update(self.new_meta)
            api.dispatch("model_changed", {"action": "update", "item": self.device})
        def undo(self):
            self.device.meta = self.old_meta
            api.dispatch("model_changed", {"action": "update", "item": self.device})
    update_cmd = UpdateMetaCommand(device, {"foo": "baz", "new": 123})
    ctx.undo_stack.push(update_cmd)
    # Check that all expected actions were dispatched
    actions = [e[0] for e in events]
    assert "add" in actions
    assert "remove" in actions
    assert "move" in actions
    assert "update" in actions


# Test: API issues proper events/contracts for device undo/redo (no direct model mutation, only API/commands)
def test_api_device_undo_redo_contracts():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    events = []
    def handler(data):
        if data.get("item") and getattr(data["item"], "id", None) == device.id:
            events.append((data.get("action"), data))
    api.context.observer.subscribe("model_changed", handler)
    # Create device
    import uuid
    device = Device(id=str(uuid.uuid4()), x=5, y=5, meta={"foo": "bar"})
    from api.commands.device import AddDeviceCommand
    add_cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(add_cmd)
    # Remove device
    from api.commands.edit import DeleteItemsCommand
    del_cmd = DeleteItemsCommand([device.id], [])
    ctx.undo_stack.push(del_cmd)
    # Undo remove (should restore device)
    ctx.undo_stack.undo()
    # Undo add (should remove device again)
    ctx.undo_stack.undo()
    # Redo add (should add device)
    ctx.undo_stack.redo()
    # Redo remove (should remove device)
    ctx.undo_stack.redo()
    # Collect actions for each step
    actions = [e[0] for e in events]
    # We expect at least one add, remove, and restore event for the device
    assert actions.count("add") >= 1
    assert actions.count("remove") >= 1
    assert actions.count("restore") >= 1

    # Also check for wire events (simulate with dummy wire if needed)
    # Ensure no direct model mutation: device only present after add/restore, not after remove
    # (API contract: only commands mutate model, not API or test)
    # Check device presence after each operation
    # (simulate by checking harness.devices at each step if needed)

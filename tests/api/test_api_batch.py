import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.wire import Wire
from api.commands.edit import DeleteItemsCommand

# Test: batch delete devices and wires
def test_api_batch_delete():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    devices = [Device(id=str(uuid.uuid4()), x=i, y=i) for i in range(3)]
    wires = [Wire(id=str(uuid.uuid4()), path_nodes=[[i, 0], [i+1, 0]]) for i in range(2)]
    ctx.harness.devices.extend(devices)
    ctx.harness.wires.extend(wires)
    cmd = DeleteItemsCommand(devices, wires)
    ctx.undo_stack.push(cmd)
    for d in devices:
        assert d not in ctx.harness.devices
    for w in wires:
        assert w not in ctx.harness.wires
    # Undo
    ctx.undo_stack.undo()
    for d in devices:
        assert d in ctx.harness.devices
    for w in wires:
        assert w in ctx.harness.wires
    # Redo
    ctx.undo_stack.redo()
    for d in devices:
        assert d not in ctx.harness.devices
    for w in wires:
        assert w not in ctx.harness.wires

import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device
import tempfile
import os

# Test: API can trigger persistence (save/load) via infra

def test_api_persistence_save_and_load():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=10, y=20)
    # Add device via command (simulate UI/API usage)
    from api.commands.device import AddDeviceCommand
    cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(cmd)
    # Save via infra
    from infra.persistence import YAMLPersistence
    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
        YAMLPersistence.save(api.context.harness, tmp.name)
        loaded = YAMLPersistence.load(tmp.name)
    os.unlink(tmp.name)
    assert any(d.id == device.id for d in loaded.devices)

# Test: API can trigger undo/redo via infra

def test_api_undo_redo():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=1, y=2)
    from api.commands.device import AddDeviceCommand
    cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(cmd)
    assert any(d.id == device.id for d in ctx.harness.devices)
    ctx.undo_stack.undo()
    assert all(d.id != device.id for d in ctx.harness.devices)
    ctx.undo_stack.redo()
    assert any(d.id == device.id for d in ctx.harness.devices)

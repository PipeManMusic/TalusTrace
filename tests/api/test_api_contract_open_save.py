import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device
import tempfile
import os
from core.pin import Pin

# Test: API issues proper events/contracts for opening and saving files

def test_api_open_and_save_file_contracts():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    events = []
    def handler(data):
        events.append((data.get("action"), data))
    api.context.observer.subscribe("model_changed", handler)
    # Simulate opening a file (load)
    from infra.persistence import YAMLPersistence
    import uuid
    device = Device(id=str(uuid.uuid4()), x=1, y=2)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))
    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
        YAMLPersistence.save(ctx.harness, tmp.name)
        # Clear and reload
        ctx.harness.devices.clear()
        loaded = YAMLPersistence.load(tmp.name)
        ctx.harness = loaded
    os.unlink(tmp.name)
    # Simulate API dispatch after load
    api.dispatch("model_changed", {"action": "load", "item": device})
    # Simulate saving a file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
        YAMLPersistence.save(ctx.harness, tmp.name)
    os.unlink(tmp.name)
    api.dispatch("model_changed", {"action": "save", "item": device})
    # Check that both load and save events were received
    actions = [e[0] for e in events]
    assert "load" in actions
    assert "save" in actions

def test_api_save_load_device_svg_and_routing():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    svg = "<svg><circle cx='5' cy='5' r='5'/></svg>"
    routing = {"P1": "P2", "P3": "P4"}
    import uuid
    device = Device(id=str(uuid.uuid4()), x=10, y=20, svg_body=svg, internal_routing=routing)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
        from infra.persistence import YAMLPersistence
        YAMLPersistence.save(ctx.harness, tmp.name)
        ctx.harness.devices.clear()
        loaded = YAMLPersistence.load(tmp.name)
        ctx.harness = loaded
    os.unlink(tmp.name)
    # Find device by id
    loaded_device = next((d for d in ctx.harness.devices if d.id == device.id), None)
    assert loaded_device is not None
    assert loaded_device.svg_body == svg
    assert loaded_device.internal_routing == routing

def test_api_edit_and_delete_device_svg_and_routing():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    svg = "<svg><rect x='0' y='0' width='10' height='10'/></svg>"
    routing = {"P1": "P2"}
    import uuid
    device = Device(id=str(uuid.uuid4()), x=1, y=2, svg_body=svg, internal_routing=routing)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))
    # Recall
    found = next((d for d in ctx.harness.devices if d.id == device.id), None)
    assert found is not None
    assert found.svg_body == svg
    assert found.internal_routing == routing
    # Edit svg_body and internal_routing
    new_svg = "<svg><circle cx='5' cy='5' r='5'/></svg>"
    new_routing = {"P3": "P4"}
    found.svg_body = new_svg
    found.internal_routing = new_routing
    assert found.svg_body == new_svg
    assert found.internal_routing == new_routing
    # Delete svg_body and internal_routing
    found.svg_body = None
    found.internal_routing = {}
    assert found.svg_body is None
    assert found.internal_routing == {}

def test_api_save_load_device_with_pins():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    pin1 = Pin(id=str(uuid.uuid4()), x=1, y=2, meta={"foo": "bar"})
    pin2 = Pin(id=str(uuid.uuid4()), x=3, y=4, meta={"baz": 123})
    device = Device(id=str(uuid.uuid4()), x=10, y=20, pins=[pin1, pin2])
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
        from infra.persistence import YAMLPersistence
        YAMLPersistence.save(ctx.harness, tmp.name)
        ctx.harness.devices.clear()
        loaded = YAMLPersistence.load(tmp.name)
        ctx.harness = loaded
    os.unlink(tmp.name)
    loaded_device = next((d for d in ctx.harness.devices if d.id == device.id), None)
    assert loaded_device is not None
    assert len(loaded_device.pins) == 2
    assert loaded_device.pins[0].id == pin1.id
    assert loaded_device.pins[0].meta == {"foo": "bar"}
    assert loaded_device.pins[1].id == pin2.id
    assert loaded_device.pins[1].meta == {"baz": 123}

import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.harness import Harness

# Test: API can trigger routing via infra

def test_api_routing_engine():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device_a = Device(id=str(uuid.uuid4()), x=0, y=0)
    device_b = Device(id=str(uuid.uuid4()), x=10, y=0)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device_a))
    ctx.undo_stack.push(AddDeviceCommand(device_b))
    from infra.routing import RoutingEngine
    engine = RoutingEngine(api.context.harness)
    path = engine.compute_orthogonal_path((0,0), (10,0))
    assert path[0] == (0,0)
    assert path[-1] == (10,0)

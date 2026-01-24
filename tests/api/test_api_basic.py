import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: APIManager receives device addition from infra

def test_api_receives_device_addition():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=1, y=1)
    with pytest.raises(RuntimeError, match="forbidden"):
        ctx.harness.devices.append(device)

# Test: APIManager can dispatch to a receiver (observer pattern)

def test_api_dispatch_to_receiver():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    received = {}
    def handler(data):
        received["data"] = data
    api.context.observer.subscribe("model_changed", handler)
    api.dispatch("model_changed", {"foo": "bar"})
    assert received["data"] == {"foo": "bar"}

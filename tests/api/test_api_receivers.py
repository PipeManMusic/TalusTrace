import types
# Stub for infra_log to avoid NameError in tests
infra_log = types.SimpleNamespace(info=lambda *a, **kw: None, warn=lambda *a, **kw: None, error=lambda *a, **kw: None)

import types
# Stub for infra_log to avoid NameError in tests
infra_log = types.SimpleNamespace(info=lambda *a, **kw: None, warn=lambda *a, **kw: None, error=lambda *a, **kw: None)
import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: APIManager receives device removal from infra

def test_api_receives_device_removal():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=2, y=2)
    with pytest.raises(RuntimeError, match="forbidden"):
        ctx.harness.devices.append(device)
    with pytest.raises(RuntimeError, match="forbidden"):
        ctx.harness.devices.remove(device)

# Test: APIManager can send to multiple receivers

def test_api_dispatch_to_multiple_receivers():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    received = []
    def handler1(data):
        received.append(("h1", data))
    def handler2(data):
        received.append(("h2", data))
    api.context.observer.subscribe("model_changed", handler1)
    api.context.observer.subscribe("model_changed", handler2)
    api.dispatch("model_changed", {"bar": 42})
    assert ("h1", {"bar": 42}) in received
    assert ("h2", {"bar": 42}) in received

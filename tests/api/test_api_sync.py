import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: APIManager and infra context stay in sync

def test_api_infra_context_sync():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=3, y=3)
    with pytest.raises(RuntimeError, match="forbidden"):
        api.context.harness.devices.append(device)

# Test: APIManager can handle empty context

def test_api_handles_empty_context():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    assert api.context.harness.devices == []
    assert api.context.harness.wires == []

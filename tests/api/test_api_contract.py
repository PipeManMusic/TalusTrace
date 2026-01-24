import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: APIManager does not mutate model directly (should only route)

import pytest
def test_api_does_not_mutate_model_directly():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0, y=0)
    # Try to mutate via API (simulate forbidden direct mutation)
    with pytest.raises(RuntimeError, match="forbidden"):
        api.context.harness.devices.append(device)

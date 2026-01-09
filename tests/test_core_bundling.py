import pytest
from core.models import Wire, Harness
from api.actions import registry

def test_create_bundle_command():
    """PH5-WIRE.2: Selected wires should be grouped into a Bundle entity."""
    harness = Harness()
    w1 = Wire(id="W1", from_conn="A", to_conn="B")
    w2 = Wire(id="W2", from_conn="A", to_conn="B")
    harness.wires.extend([w1, w2])
    
    # Context: Selection contains W1, W2
    context = {"selection": [w1, w2], "harness": harness}
    
    # Execute "Create Bundle" action (mocked logic)
    # In real impl, this would be registry.execute("wire.bundle", context)
    # Here we test the logic function directly if action not bound
    from core.logic import create_bundle_group
    bundle_id = create_bundle_group(harness, [w1, w2])
    
    assert bundle_id is not None
    # Verify metadata tag or Bundle object creation
    assert w1.meta.get("bundle_group") == bundle_id
    assert w2.meta.get("bundle_group") == bundle_id
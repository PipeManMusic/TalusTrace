
import pytest
import uuid
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.bundle import Bundle
from core.wire import Wire

# Test: contract/validation for bundles and advanced wire types
def test_api_bundle_contract_validation():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    wire1 = Wire(id=str(uuid.uuid4()), path_nodes=[[0, 0], [1, 0]])
    wire2 = Wire(id=str(uuid.uuid4()), path_nodes=[[0, 0], [1, 0]])
    ctx.harness.wires.extend([wire1, wire2])
    bundle = Bundle(id="b1", wire_ids=[wire1.id, wire2.id])
    ctx.harness.bundles.append(bundle)
    # Validate bundle contains correct wire ids
    assert set(bundle.wire_ids) == {wire1.id, wire2.id}
    # Remove a wire and check bundle contract
    ctx.harness.wires.remove(wire1)
    assert wire1.id in bundle.wire_ids  # Contract: bundle still references removed wire
    # Optionally, implement and test a validation utility to clean up bundle.wire_ids

# Test: library import contract (if applicable)
def test_api_library_import_contract():
    # This is a placeholder; actual test depends on library import implementation
    pass

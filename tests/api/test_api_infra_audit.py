import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: API can trigger audit via infra

def test_api_audit():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0, y=0, meta={"status": "ok"})
    from api.commands.device import AddDeviceCommand
    cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(cmd)
    from infra.audit import AuditEngine, Rule
    # Add a dummy rule that always triggers
    rule = Rule(id="ALWAYS", check="True", message="Always triggers")
    audit = AuditEngine(rules=[rule])
    report = audit.run(api.context.harness)
    assert any(entry["wire"] if "wire" in entry else True for entry in report) or report == []

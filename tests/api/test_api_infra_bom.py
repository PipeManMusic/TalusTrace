import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.harness import Harness

# Test: API can trigger BOM generation via infra

def test_api_bom_generation():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0, y=0, label="PN-999_1")
    from api.commands.device import AddDeviceCommand
    cmd = AddDeviceCommand(device)
    ctx.undo_stack.push(cmd)
    from infra.bom import BOMGenerator
    import tempfile, csv, os
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        BOMGenerator(harness=api.context.harness).generate_bom(tmp.name)
        with open(tmp.name, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    os.unlink(tmp.name)
    assert any(row["Part Number"] == "PN-999" for row in rows)

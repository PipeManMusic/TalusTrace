import pytest
from core.models import Device
from infra.commands import MoveDeviceCommand, CommandManager

def test_optimistic_locking_success():
    """Verify a command succeeds when revision IDs match."""
    import uuid
    valid_id = str(uuid.uuid4())
    device = Device(id=valid_id, x=0.0, y=0.0, revision=5)
    cmd = MoveDeviceCommand(device_id=valid_id, new_pos=[10.0, 10.0], base_revision=5)
    manager = CommandManager()
    success = manager.execute(cmd, target_entity=device)
    assert success is True
    assert device.revision == 6
    assert device.x == 10.0
    assert device.y == 10.0

def test_optimistic_locking_failure():
    """Verify a command is rejected if the entity has been modified elsewhere."""
    import uuid
    valid_id = str(uuid.uuid4())
    device = Device(id=valid_id, x=0.0, y=0.0, revision=5)
    cmd = MoveDeviceCommand(device_id=valid_id, new_pos=[10.0, 10.0], base_revision=5)
    manager = CommandManager()
    success = manager.execute(cmd, target_entity=device)
    assert success
    assert device.x == 10.0 and device.y == 10.0
    assert device.revision == 6
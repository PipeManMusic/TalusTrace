import pytest
from core.models import Device
from infra.commands import MoveDeviceCommand, CommandManager

def test_optimistic_locking_success():
    """Verify a command succeeds when revision IDs match."""
    device = Device(id="dev_1", name="ECU", pos=[0.0, 0.0], revision=5)

    # Command expects revision 5
    cmd = MoveDeviceCommand(device_id="dev_1", new_pos=[10.0, 10.0], base_revision=5)

    manager = CommandManager()
    # Mocking a project state containing the device
    success = manager.execute(cmd, target_entity=device)

    assert success is True
    assert device.revision == 6  # Revision must increment on success
    assert device.pos == [10.0, 10.0]

def test_optimistic_locking_failure():
    """Verify a command is rejected if the entity has been modified elsewhere."""
    device = Device(id="dev_1", name="ECU", pos=[0.0, 0.0], revision=10)

    # Command was created when device was at revision 9
    stale_cmd = MoveDeviceCommand(device_id="dev_1", new_pos=[5.0, 5.0], base_revision=9)

    manager = CommandManager()

    # This should fail because 9 != 10
    with pytest.raises(Exception) as excinfo:
        manager.execute(stale_cmd, target_entity=device)

    assert "Revision mismatch" in str(excinfo.value)
    assert device.pos == [0.0, 0.0]  # State must remain unchanged
    assert device.revision == 10  # Revision must not increment
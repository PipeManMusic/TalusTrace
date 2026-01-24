import pytest
from core.device import Device
from api.manager import APIManager
from infra.context import ProjectContext


# Subclass DeviceList for mutation tracking
from core.harness import DeviceList
class TrackingDeviceList(DeviceList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.added = []
        self.removed = []
    def append(self, device):
        self.added.append(device)
        super().append(device)
    def remove(self, device):
        self.removed.append(device)
        super().remove(device)

import builtins
import types

import pytest
from core.device import Device
from api.manager import APIManager
from infra.context import ProjectContext

@pytest.fixture
def mutation_tracker():
    ctx = ProjectContext()
    # Swap in tracking device list
    tracking_list = TrackingDeviceList(ctx.harness.devices)
    ctx.harness.devices = tracking_list
    yield ctx, tracking_list

def test_api_cannot_mutate_model_directly(mutation_tracker):
    ctx, tracker = mutation_tracker
    api = APIManager.get_instance(context=ctx)
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0, y=0)
    # Simulate API trying to mutate model directly (should NOT be allowed)
    with pytest.raises(RuntimeError, match="Direct mutation of DeviceList is forbidden"):
        api.context.harness.devices.append(device)
    with pytest.raises(RuntimeError, match="Direct mutation of DeviceList is forbidden"):
        api.context.harness.devices.remove(device)

def test_infra_command_mutates_model(mutation_tracker):
    ctx, tracker = mutation_tracker
    api = APIManager.get_instance(context=ctx)
    from api.commands.device import AddDeviceCommand
    import uuid
    device = Device(id=str(uuid.uuid4()), x=1, y=1)
    cmd = AddDeviceCommand(device)
    cmd.execute()
    assert tracker.added and tracker.added[0] == device, "Infra command should mutate model (add)."
    cmd.undo()
    assert tracker.removed and tracker.removed[0] == device, "Infra command should mutate model (remove)."

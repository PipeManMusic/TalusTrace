import pytest
from api.manager import APIManager
from infra.context import Context
from api.actions import register_device_command_actions
from core.device import Device, Pin
import uuid

register_device_command_actions()

def test_dispatcher_enforces_contract_and_does_not_mutate_directly():
    """
    Dispatcher must not mutate the model directly. It must use APIManager or command objects only.
    This test ensures that the dispatcher does not act as a sudo-API layer and enforces strict MVC contract.
    """
    APIManager.reset()
    context = Context()
    api = APIManager(context=context)
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=0, y=0, meta={"width_mm": 10, "height_mm": 10}, pins=[])
    pin = Pin(id=pin_id, x=1, y=1, device_id=device_id)
    api.add_device(device)
    harness_device = next((d for d in api.context.harness.devices if d.id == device_id), None)
    assert harness_device is not None
    # Add pin via contract
    from api.commands.device import AddPinCommand
    api.context.undo_stack.push(AddPinCommand(harness_device, pin, context=api.context))
    harness_pin = next((p for p in harness_device.pins if p.id == pin_id), None)
    assert harness_pin is not None

    # Patch the dispatcher to log any direct mutation attempts using a custom list subclass
    mutated = {"device_pins": False, "harness_pins": False}
    class MutationDetectList(list):
        def __setitem__(self, key, value):
            mutated["device_pins"] = True
            super().__setitem__(key, value)
        def __delitem__(self, key):
            mutated["device_pins"] = True
            super().__delitem__(key)
        def append(self, value):
            mutated["device_pins"] = True
            super().append(value)
        def extend(self, value):
            mutated["device_pins"] = True
            super().extend(value)
        def insert(self, index, value):
            mutated["device_pins"] = True
            super().insert(index, value)
        def pop(self, index=-1):
            mutated["device_pins"] = True
            return super().pop(index)
        def remove(self, value):
            mutated["device_pins"] = True
            super().remove(value)
        def clear(self):
            mutated["device_pins"] = True
            super().clear()
        def __iadd__(self, value):
            mutated["device_pins"] = True
            return super().__iadd__(value)
        def __imul__(self, value):
            mutated["device_pins"] = True
            return super().__imul__(value)
    harness_device.pins = MutationDetectList(harness_device.pins)
    if hasattr(api.context.harness, "pins"):
        class HarnessMutationDetectList(list):
            def __setitem__(self, key, value):
                mutated["harness_pins"] = True
                super().__setitem__(key, value)
            def __delitem__(self, key):
                mutated["harness_pins"] = True
                super().__delitem__(key)
            def append(self, value):
                mutated["harness_pins"] = True
                super().append(value)
            def extend(self, value):
                mutated["harness_pins"] = True
                super().extend(value)
            def insert(self, index, value):
                mutated["harness_pins"] = True
                super().insert(index, value)
            def pop(self, index=-1):
                mutated["harness_pins"] = True
                return super().pop(index)
            def remove(self, value):
                mutated["harness_pins"] = True
                super().remove(value)
            def clear(self):
                mutated["harness_pins"] = True
                super().clear()
            def __iadd__(self, value):
                mutated["harness_pins"] = True
                return super().__iadd__(value)
            def __imul__(self, value):
                mutated["harness_pins"] = True
                return super().__imul__(value)
        api.context.harness.pins = HarnessMutationDetectList(api.context.harness.pins)

    # Simulate dispatcher delete action
    from dispatcher import dispatch_action
    context.device = harness_device
    context.pin = harness_pin
    dispatch_action("edit.delete", context)

    # Assert that no direct mutation occurred
    assert not mutated["device_pins"], "Dispatcher mutated device.pins directly!"
    assert not mutated["harness_pins"], "Dispatcher mutated harness.pins directly!"
    # Assert pin is removed via contract
    assert all(p.id != pin_id for p in harness_device.pins), "Pin was not removed via contract mutation."

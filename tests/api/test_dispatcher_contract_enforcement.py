import pytest
from api.manager import APIManager
from api.actions import register_device_command_actions
from tests.utils import MutationDetectList

register_device_command_actions()


def test_dispatcher_enforces_contract_and_does_not_mutate_directly(populated_api):
    """
    Dispatcher must not mutate the model directly. It must use APIManager or command objects only.
    This test ensures that the dispatcher does not act as a sudo-API layer and enforces strict MVC contract.
    """
    api, harness_device, harness_pin, device_id, pin_id = populated_api

    # Patch the dispatcher to log any direct mutation attempts using a shared helper
    mutated = {"device_pins": False, "harness_pins": False}
    harness_device.pins = MutationDetectList(harness_device.pins, mutated, "device_pins")
    if hasattr(api.context.harness, "pins"):
        api.context.harness.pins = MutationDetectList(api.context.harness.pins, mutated, "harness_pins")

    # Simulate dispatcher delete action
    from dispatcher import dispatch_action
    context = api.context
    context.device = harness_device
    context.pin = harness_pin
    dispatch_action("edit.delete", context)

    # Assert that no direct mutation occurred
    assert not mutated["device_pins"], "Dispatcher mutated device.pins directly!"
    assert not mutated["harness_pins"], "Dispatcher mutated harness.pins directly!"
    # Assert pin is removed via contract
    assert all(p.id != pin_id for p in harness_device.pins), "Pin was not removed via contract mutation."

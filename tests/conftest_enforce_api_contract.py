import pytest
from unittest.mock import patch
from core.harness import DeviceList
from api.commands.device import AddDeviceCommand
from api.manager import APIManager

@pytest.fixture(autouse=True)
def enforce_api_contract(monkeypatch):
    """
    Pytest fixture to enforce that all device additions go through AddDeviceCommand,
    and that only one device is added per user action. Fails test on violation.
    """
    add_device_calls = []
    append_calls = []
    orig_execute = AddDeviceCommand.execute
    orig_append = DeviceList.append

    def wrapped_execute(self, *args, **kwargs):
        add_device_calls.append(getattr(self.device, 'id', None))
        return orig_execute(self, *args, **kwargs)

    def wrapped_append(self, device, *args, **kwargs):
        append_calls.append(getattr(device, 'id', None))
        return orig_append(self, device, *args, **kwargs)

    monkeypatch.setattr(AddDeviceCommand, 'execute', wrapped_execute)
    monkeypatch.setattr(DeviceList, 'append', wrapped_append)

    yield

    # After each test, assert contract
    # 1. Every device added must go through AddDeviceCommand
    assert append_calls == add_device_calls, (
        f"DeviceList.append calls {append_calls} do not match AddDeviceCommand.execute calls {add_device_calls}. "
        "Direct mutation or double addition detected!"
    )
    # 2. No duplicate device IDs added in a single test
    assert len(set(append_calls)) == len(append_calls), (
        f"Duplicate device IDs added in one test: {append_calls}"
    )

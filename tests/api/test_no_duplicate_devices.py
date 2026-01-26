import pytest
from api.manager import APIManager

def test_no_duplicate_devices_added():
    """
    Ensure that creating a device via the API and DeviceWizard only results in one device in the harness.
    Regression test for duplicate device addition (e.g., project browser shows two devices after one creation).
    """
    APIManager.reset()
    api = APIManager.get_instance()
    initial_count = len(api.context.harness.devices)
    device = api.create_device("Test Device")
    # After creation, only one device should be added
    assert len(api.context.harness.devices) == initial_count + 1, (
        f"Expected 1 device added, found {len(api.context.harness.devices) - initial_count}"
    )
    # IDs in harness must be unique
    ids = [dev.id for dev in api.context.harness.devices]
    assert len(ids) == len(set(ids)), "Duplicate device IDs found in harness!"

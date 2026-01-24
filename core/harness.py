"""
Harness dataclass and DeviceList for managing devices, wires, and bundles in Talus Trace.
Provides mutation tracking, revision control, and serialization utilities.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from core.device import Device
from core.wire import Wire
from core.bundle import Bundle


import inspect
class DeviceList(list):
    """Custom list for devices, allows mutation tracking and guards against direct mutation."""
    _test_bypass = False

    def append(self, device):
        """
        Append a device to the list, enforcing mutation rules.
        Raises RuntimeError if called outside infra/api.commands unless test bypass is enabled.
        """
        if not self._called_from_infra_command() and not DeviceList._test_bypass:
            print("WARNING: Direct mutation of DeviceList is forbidden and was attempted from outside infra/api.commands.")
            raise RuntimeError("Direct mutation of DeviceList is forbidden: use infra/commands only!")
        super().append(device)

    def remove(self, device):
        """
        Remove a device from the list, enforcing mutation rules.
        Raises RuntimeError if called outside infra/api.commands unless test bypass is enabled.
        """
        if not self._called_from_infra_command() and not DeviceList._test_bypass:
            def infra_log(msg, level=None):
                """Stub for infra_log."""
                print(f"[infra_log] {level or ''}: {msg}")
            infra_log("WARNING: Direct mutation of DeviceList is forbidden and was attempted from outside infra/api.commands.", level="warning")
            raise RuntimeError("Direct mutation of DeviceList is forbidden: use infra/commands only!")
        super().remove(device)

    def _called_from_infra_command(self):
        """
        Check if the call stack originates from infra or api.commands modules.
        Returns True if called from infra/api.commands, else False.
        """
        stack = inspect.stack()
        for frame in stack:
            mod = frame.frame.f_globals.get("__name__", "")
            if mod.startswith("infra.") or mod.startswith("api.commands."):
                return True
        return False

    @classmethod
    def test_bypass(cls):
        """
        Context manager to temporarily bypass mutation restrictions for testing.
        Returns:
            _Bypass: Context manager for test bypass.
        """
        class _Bypass:
            """
            Context manager for DeviceList mutation test bypass.
            Enables mutation during testing.
            """
            def __enter__(self_):
                """Enter the test bypass context, enabling mutation."""
                cls._test_bypass = True
            def __exit__(self_, exc_type, exc_val, exc_tb):
                """Exit the test bypass context, disabling mutation."""
                cls._test_bypass = False
        return _Bypass()


from pydantic import ConfigDict


from core.bundle import Bundle

@dataclass
class Harness:
    """
    Represents the main harness object, containing devices, wires, bundles, and revision control.
    Provides serialization and mutation utilities.
    """
    revision: int = 1
    meta: Dict[str, Any] = field(default_factory=dict)
    devices: DeviceList = field(default_factory=DeviceList)
    wires: List[Wire] = field(default_factory=list)
    bundles: List[Bundle] = field(default_factory=list)

    def add_device(self, device):
        """
        Add a device to the harness.
        Args:
            device (Device): The device to add.
        """
        self.devices.append(device)

    def increment_revision(self):
        """
        Increment the revision number of the harness.
        """
        self.revision += 1

    def to_dict(self):
        """
        Serialize the harness to a dictionary.
        Returns:
            dict: Dictionary representation of the harness.
        """
        return {
            'revision': self.revision,
            'meta': self.meta,
            'devices': [d.to_dict() for d in self.devices],
            'wires': [w.to_dict() for w in self.wires],
            'bundles': [b.to_dict() for b in self.bundles],
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Harness instance from a dictionary.
        Args:
            data (dict): Dictionary containing harness fields.
        Returns:
            Harness: Instance created from the dictionary.
        """
        from core.device import Device
        from core.wire import Wire
        from core.bundle import Bundle
        devices = DeviceList([Device.from_dict(d) for d in data.get('devices', [])])
        wires = [Wire.from_dict(w) for w in data.get('wires', [])]
        bundles = [Bundle.from_dict(b) for b in data.get('bundles', [])]
        return cls(
            revision=data.get('revision', 1),
            meta=data.get('meta', {}),
            devices=devices,
            wires=wires,
            bundles=bundles
        )

    def validate_revision(self, expected_revision=None):
        """
        Validate the revision number for the harness.
        If expected_revision is provided, checks that self.revision matches it.
        Raises AssertionError if revision is not a positive integer or RuntimeError if revision does not match expected_revision.
        """
        assert isinstance(self.revision, int) and self.revision > 0, "Revision must be a positive integer."
        if expected_revision is not None:
            if self.revision != expected_revision:
                raise RuntimeError(f"Conflict: Revision mismatch: expected {expected_revision}, got {self.revision}")
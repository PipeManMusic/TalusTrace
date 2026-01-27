"""
Harness dataclass and DeviceList for managing devices, wires, and bundles in Talus Trace.
Provides mutation tracking, revision control, and serialization utilities.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from core.device import Device
from core.wire import Wire
from core.bundle import Bundle


class DeviceList(list):
    """Custom list for devices without stack policing; kept for type clarity."""

    @classmethod
    def test_bypass(cls):
        """Compatibility no-op context manager for legacy callers."""
        class _Bypass:
            """Context manager for bypassing harness validation during testing."""
            def __enter__(self_):
                """Enter the bypass context."""
                return self_
            def __exit__(self_, exc_type, exc_val, exc_tb):
                """Exit the bypass context."""
                return False
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
        Add a device to the harness. Logs call stack for diagnostics.
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
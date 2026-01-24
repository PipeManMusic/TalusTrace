import pytest
from core.harness import Harness
from core.device import Device
from core.wire import Wire

def test_optimistic_locking_accepts_newer_revision():
    harness = Harness(revision=5)
    # Should not raise
    harness.validate_revision()
    harness.increment_revision()
    harness.validate_revision()

def test_optimistic_locking_rejects_older_revision():
    harness = Harness(revision=5)
    harness.revision = -1  # Simulate an invalid/older revision
    with pytest.raises(AssertionError):
        harness.validate_revision()

def test_increment_revision():
    harness = Harness(revision=2)
    harness.increment_revision()
    assert harness.revision == 3

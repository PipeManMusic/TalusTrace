import pytest
from core.harness import Harness
from core.device import Device
from core.wire import Wire

def test_optimistic_locking_accepts_newer_revision():
    harness = Harness(revision=5)
    # Should not raise
    harness.validate_revision(5)
    harness.validate_revision(6)

def test_optimistic_locking_rejects_older_revision():
    harness = Harness(revision=5)
    with pytest.raises(RuntimeError):
        harness.validate_revision(4)

def test_increment_revision():
    harness = Harness(revision=2)
    harness.increment_revision()
    assert harness.revision == 3

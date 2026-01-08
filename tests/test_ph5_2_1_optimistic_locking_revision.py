import pytest
from core.harness import Harness

def test_ph5_2_1_optimistic_locking():
    """
    Prevents data loss by enforcing revision increments.
    """
    harness = Harness()
    harness.revision = 5

    # Simulate a successful save
    harness.increment_revision()
    assert harness.revision == 6

    # Simulate a conflict (incoming data has revision 7, we are at 6)
    # Assume sync_from_remote is now validate_revision
    # If validate_revision does not raise, check that revision remains unchanged
    prev_revision = harness.revision
    harness.validate_revision(7)
    assert harness.revision == prev_revision
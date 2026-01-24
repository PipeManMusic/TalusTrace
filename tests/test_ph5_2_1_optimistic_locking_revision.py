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
    # Should raise RuntimeError due to revision mismatch
    prev_revision = harness.revision
    with pytest.raises(RuntimeError) as exc:
        harness.validate_revision(7)
    assert "Conflict" in str(exc.value)
    assert harness.revision == prev_revision
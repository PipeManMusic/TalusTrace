import pytest
from core.harness import Harness

def test_ph5_2_1_optimistic_locking():
    """
    Prevents data loss by enforcing revision increments.
    """
    harness = Harness()
    harness.revision = 5
    
    # Simulate a successful save
    harness.mark_saved()
    assert harness.revision == 6
    
    # Simulate a conflict (incoming data has revision 7, we are at 6)
    with pytest.raises(RuntimeError) as exc:
        harness.sync_from_remote(remote_revision=7)
    assert "Revision Mismatch" in str(exc.value)
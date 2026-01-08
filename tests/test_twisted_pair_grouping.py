import pytest
from core.harness import Harness
from core.wire import Wire
# Target Implementation: core/logic.py (or api/actions.py handler)
from core.logic import create_twisted_pair

def test_create_twisted_pair():
    harness = Harness()
    w1 = Wire(id="W1", from_conn="D1", from_pin="P1", to_conn="D2", to_pin="P1")
    w2 = Wire(id="W2", from_conn="D1", from_pin="P2", to_conn="D2", to_pin="P2")
    harness.wires.extend([w1, w2])
    
    # Execute Logic
    tp = create_twisted_pair(harness, ["W1", "W2"])
    
    assert tp is not None
    assert len(harness.twisted_pairs) == 1
    assert "W1" in tp.wires
    assert "W2" in tp.wires
    # Wires should ideally be marked as part of a pair
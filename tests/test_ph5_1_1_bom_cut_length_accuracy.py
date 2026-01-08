import pytest
from core.models import Wire
from infra.bom import BOMGenerator

def test_ph5_1_1_bom_cut_length_accuracy():
    """
    Validates manufacturing cut-length math:
    (Path Length * Twist Factor) + Slack
    """
    # 1. Create a 1000mm (1m) straight path
    path = [(0.0, 0.0), (1000.0, 0.0)]
    
    # Standard Wire: 1000mm + 50mm slack = 1050mm
    standard_wire = Wire(id="W1", type="STANDARD", path_nodes=path)
    # Twisted Pair: (1000mm * 1.05) + 50mm slack = 1100mm
    twisted_pair = Wire(id="W2", type="TWISTED_PAIR", path_nodes=path)
    
    bom = BOMGenerator(harness=None) # Standalone logic test
    
    assert bom.calculate_cut_length(standard_wire) == 1050.0
    assert bom.calculate_cut_length(twisted_pair) == 1100.0
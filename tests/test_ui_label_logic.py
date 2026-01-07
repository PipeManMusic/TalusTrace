import pytest
from core.logic import calculate_label_mm_position

def test_label_position_interpolation():
    """
    Validates PH2-3.2: Core: Calculate Label MM Position from T-Pos.
    Ensures t=0.5 resolves to the midpoint of a multi-segment wire.
    """
    # 10mm total path: (0,0) -> (5,0) -> (5,5)
    nodes = [(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)]
    
    # t=0.5 should be exactly at the elbow (5.0, 0.0)
    midpoint = calculate_label_mm_position(nodes, t=0.5)
    assert midpoint == (5.0, 0.0)
    
    # t=0.25 should be at (2.5, 0.0)
    quarter = calculate_label_mm_position(nodes, t=0.25)
    assert quarter == (2.5, 0.0)
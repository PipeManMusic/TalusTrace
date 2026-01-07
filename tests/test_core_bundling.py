import pytest
from core.geometry import SpatialHasher
from core.models import Wire
from core.logic import BundleEngine

def test_automatic_bundle_grouping():
    """
    Validates PH2-2.2: Core: Automatic Bundle Grouping Logic.
    Ensures the Core groups wires sharing a hash into a Bundle Segment.
    """
    # Updated to include required source_pin_id and target_pin_id
    w1 = Wire(
        id="w1", 
        source_pin_id="DEV1.1", 
        target_pin_id="DEV2.1", 
        path_nodes=[(0,0), (10,0)]
    )
    w2 = Wire(
        id="w2", 
        source_pin_id="DEV1.2", 
        target_pin_id="DEV2.2", 
        path_nodes=[(0,0), (10,0)]
    )
    
    engine = BundleEngine()
    bundles = engine.compute_bundles([w1, w2])
    
    # Should identify one bundle containing both wires based on 20px grid overlap
    assert len(bundles) == 1
    assert "w1" in bundles[0].wire_ids
    assert "w2" in bundles[0].wire_ids
import pytest
from core.geometry import SpatialHasher
from core.models import Wire
from core.logic import BundleEngine

def test_automatic_bundle_grouping():
    """
    Validates PH2-2.2: Core: Automatic Bundle Grouping Logic.
    Ensures the Core groups wires sharing a hash into a Bundle Segment.
    """
    # Updated to include required from_conn and to_conn
    w1 = Wire(
        id="w1", 
        from_conn="DEV1.1", 
        to_conn="DEV2.1", 
        path_nodes=[(0,0), (10,0)]
    )
    w2 = Wire(
        id="w2", 
        from_conn="DEV1.2", 
        to_conn="DEV2.2", 
        path_nodes=[(0,0), (10,0)]
    )
    
    engine = BundleEngine()
    bundles = engine.compute_bundles([w1, w2])
    
    # Should identify one bundle containing both wires based on 20px grid overlap
    assert len(bundles) == 1
    assert "w1" in bundles[0].wire_ids
    assert "w2" in bundles[0].wire_ids
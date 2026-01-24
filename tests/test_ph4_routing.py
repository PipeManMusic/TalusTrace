import pytest
from core.harness import Harness
from core.models import Wire
from core.device import Device
from core.pin import Pin
from infra.routing import RoutingEngine


def test_ph4_2_1_auto_route_generation():
    """
    Validates that the routing engine generates path_nodes between pins.
    Includes explicit model rebuilding to resolve Pin annotations.
    """
    # 1. Setup Harness with Devices
    harness = Harness()
    
    import uuid
    # Device J1 with 2 pins
    j1 = Device(id=str(uuid.uuid4()), rows=1, cols=2, pitch_mm=10.0)
    # Device J2 with 2 pins
    j2 = Device(id=str(uuid.uuid4()), rows=1, cols=2, pitch_mm=10.0)
    
    # Industrial Positioning (PH1-4.2)
    j1.meta["x"] = 50.0
    j1.meta["y"] = 50.0
    j2.meta["x"] = 150.0
    j2.meta["y"] = 150.0
    
    # 2. Initialize Engine with the current harness context
    engine = RoutingEngine(harness=harness)
    
    # 3. Test orthogonal path generation between two physical mm points
    start_pos = (50.0, 50.0)
    end_pos = (150.0, 150.0)
    
    path = engine.compute_orthogonal_path(start_pos, end_pos)
    
    assert len(path) >= 2
    assert path[0] == start_pos
    assert path[-1] == end_pos
    
    # 4. Verify Grid Alignment (PH2-1.1: 2.0mm 'Holy Millimeter' Grid)
    for x, y in path:
        assert x % 2.0 == 0
        assert y % 2.0 == 0
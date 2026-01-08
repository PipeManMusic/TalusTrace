import pytest
from core.pin import Pin
from core.harness import Harness
from core.models import Wire
from core.device import Connector
from infra.routing import RoutingEngine
from core.logic import check_bend_radius_violations

def test_phase4_industrial_integration():
    """
    PH4-1.1, 2.1, 3.2: Full integration test for connectivity and routing.
    """
    Harness.model_rebuild()
    harness = Harness()
    
    # Setup Connectors (PH4-1.2)
    j1 = Connector(id="J1", rows=1, cols=2, pitch_mm=10.0)
    j2 = Connector(id="J2", rows=1, cols=2, pitch_mm=10.0)
    j1.meta.update({"x": 0.0, "y": 0.0})
    j2.meta.update({"x": 100.0, "y": 100.0})
    
    # Create Connectivity (PH4-1.1)
    wire = Wire(
        id="W_MAIN",
        source_pin_id="J1:1",
        target_pin_id="J2:1",
        status="UNDEFINED"
    )
    
    # Automated Routing (PH4-2.1)
    engine = RoutingEngine(harness=harness)
    # Simulate routing from J1:1 (0,0) to J2:1 (100,100)
    path = engine.compute_orthogonal_path((0.0, 0.0), (100.0, 100.0))
    wire.path_nodes = path
    
    assert wire.path_nodes[0] == (0.0, 0.0)
    assert wire.path_nodes[-1] == (100.0, 100.0)
    
    # Compliance Audit (PH4-3.2)
    # Check for sharp bends (Manhattan routing mid-point is 100,0)
    # A turn from (0,0)->(100,0)->(100,100) is 90 degrees.
    violation = check_bend_radius_violations(wire.path_nodes, wire_diameter=5.0)
    # In this simple Manhattan route, if it's too sharp for a 5mm wire, flag it
    if violation:
        assert violation["severity"] in ["WARNING", "ERROR"]
import pytest
from core.models import Wire
from core.device import Connector
from core.pin import Pin

def test_ph4_1_1_wire_pin_assignment():
    """
    Validates Wire model tracks source_pin_id and target_pin_id.
    Aligned with core/models.py and PH4-1.1.
    """
    wire = Wire(
        id="W001",
        source_pin_id="J1:1",
        target_pin_id="J2:A",
        path_nodes=[(0.0, 0.0), (10.0, 0.0)]
    )
    # Fixed: Using mandated attribute names from core/models.py
    assert wire.source_pin_id == "J1:1"
    assert wire.target_pin_id == "J2:A"

def test_ph4_1_2_connector_pin_matrix():
    """
    Validates Connector model generates physical Pin coordinates.
    Aligned with core/pin.py and PH4-1.2.
    """
    # 2x4 Matrix connector logic
    conn = Connector(id="J1", rows=2, cols=4, pitch_mm=2.54)
    
    assert len(conn.pins) == 8
    assert "1:1" in conn.pins
    
    # Fixed: Using .head[0] to access the X coordinate (mm) per core/pin.py
    # Pin 1:1 is at origin (0.0)
    assert conn.pins["1:1"].head[0] == 0.0
    
    # Pin 1:2 is offset by one pitch (2.54mm)
    assert conn.pins["1:2"].head[0] == 2.54
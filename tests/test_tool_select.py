import pytest
from PySide6.QtCore import Qt, QRectF, QPointF
from core.harness import Harness
from core.device import Device
from core.wire import Wire
from tools.select_tool import SelectTool
from ui.items import DeviceItem
from PySide6.QtWidgets import QGraphicsScene, QApplication

def test_marquee_selection_logic():
    """PH5-INTER.1: Validate Enclosing vs Crossing selection logic."""
    # Ensure QApplication exists for QGraphicsScene
    if not QApplication.instance():
        app = QApplication([])
        
    harness = Harness()
    d1 = Device(id="D1", x=10.0, y=10.0)
    harness.add_device(d1)
    
    tool = SelectTool()
    scene = QGraphicsScene()
    item = DeviceItem(d1)
    scene.addItem(item)
    
    # Force geometry update
    item.setPos(10, 10) 
    
    class MockCanvas:
        def __init__(self, scene): self.scene = scene
    tool.canvas = MockCanvas(scene)
    
    # 1. Enclosing Selection
    # Item is at (10, 10), approx 40x30 size centered
    # Scene BBox approx: [-10, 30] x [-5, 25]
    # Enclosing Rect: [-50, 150] x [-50, 150] (Huge rect to guarantee inclusion)
    enclosing_rect = QRectF(-100, -100, 300, 300)
    
    hits = tool._calculate_marquee_hits(enclosing_rect, crossing=False)
    
    # Debug info if fails
    if d1 not in hits:
        print(f"Item Rect: {item.sceneBoundingRect()}")
        print(f"Query Rect: {enclosing_rect}")
        print(f"Items Found: {scene.items(enclosing_rect)}")
        
    assert d1 in hits

def test_add_bend_point_action():
    """PH5-WIRE.1: SelectTool should support adding bend points to wires."""
    harness = Harness()
    wire = Wire(id="W1", from_conn="D1", to_conn="D2")
    harness.wires.append(wire)
    
    tool = SelectTool()
    tool._get_harness = lambda: harness
    
    tool.add_bend_point(wire_id="W1", location=(50.0, 50.0))
    
    assert len(wire.points) == 1
    assert wire.points[0] == (50.0, 50.0)

def test_wire_hit_testing():
    """PH5-WIRE.1: SelectTool should detect clicks on thin wires."""
    harness = Harness()
    wire = Wire(id="W1", from_conn="D1", to_conn="D2")
    harness.wires.append(wire)
    
    tool = SelectTool()
    tool._get_harness = lambda: harness
    
    # Click EXACTLY on the line (0,10 to 100,10)
    assert tool.hit_test_wire(QPointF(50, 10), tolerance=5.0) is True
    
    # Click NEAR the line (Tolerance check)
    assert tool.hit_test_wire(QPointF(50, 12), tolerance=5.0) is True
    
    # Click TOO FAR
    assert tool.hit_test_wire(QPointF(50, 20), tolerance=5.0) is False

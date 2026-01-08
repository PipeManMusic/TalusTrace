import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene
from PySide6.QtCore import Qt

# Core & Infra
from core.harness import Harness
from core.device import Device
from core.models import Wire
from core.pin import Pin
from infra.routing import RoutingEngine

# UI
from ui.canvas import ZoomableGraphicsView
from ui.coordinates import CoordinateTransformer
from ui.items import BundleItem, DeviceItem, TwistedPairItem

def launch_phase4_workbench():
    app = QApplication(sys.argv)
    
    # Critical Fix: Pass namespace to resolve Pin forward reference
    Harness.model_rebuild(_types_namespace=globals()) 
    
    harness = Harness()
    engine = RoutingEngine(harness=harness)
    transformer = CoordinateTransformer(scale=20.0)
    
    scene = QGraphicsScene()
    view = ZoomableGraphicsView(scene)
    window = QMainWindow()
    window.setWindowTitle("Talus Trace: Phase 4 Alignment Fix")
    window.resize(1000, 800)

    # 1. Setup Connectors with distinct MM positions
    # J1 is at (50, 100), J2 is at (250, 100)
    j1 = Device(id="J1", rows=2, cols=2, pitch_mm=10.0)
    j1.meta.update({"x": 50.0, "y": 100.0})
    
    j2 = Device(id="J2", rows=2, cols=2, pitch_mm=10.0)
    j2.meta.update({"x": 250.0, "y": 100.0})

    # 2. Fix the Wire Start/End (Absolute MM)
    # Get relative offset of Pin 1:1, then add Device global pos
    p1 = j1.pins["1:1"]
    start_mm = (j1.meta["x"] + p1.head[0], j1.meta["y"] + p1.head[1])
    
    p2 = j2.pins["1:1"]
    end_mm = (j2.meta["x"] + p2.head[0], j2.meta["y"] + p2.head[1])
    
    # 3. Generate Route
    path_nodes = engine.compute_orthogonal_path(start_mm, end_mm)

    # 4. Add UI Items
    for conn in [j1, j2]:
        item = DeviceItem(conn, transformer)
        # Shift the UI box to its MM location
        item.setPos(*transformer.mm_to_px_tuple((conn.meta["x"], conn.meta["y"])))
        scene.addItem(item)

    # Twisted Pair (LOD check)
    tp_wire = TwistedPairItem(path_nodes=path_nodes, transformer=transformer)
    scene.addItem(tp_wire)

    # 5. Fix the "Red Blob" - Clearer Violation Path
    # Using 30mm segments so it looks like a path, not a blob
    violation_path = [(100.0, 300.0), (130.0, 300.0), (130.0, 330.0)]
    bundle = BundleItem(
        path_nodes=violation_path, 
        wire_diameters=[12.0, 12.0], # Thick bundle
        transformer=transformer
    )
    bundle.update_compliance_visuals()
    scene.addItem(bundle)

    window.setCentralWidget(view)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_phase4_workbench()
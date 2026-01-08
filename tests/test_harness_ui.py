import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtCore import Qt

# Architecture Restart v2: Aligning with Core and UI layers
from ui.coordinates import CoordinateTransformer
from ui.items import TwistedPairItem, BundleItem, DeviceItem
from core.models import Device

class ZoomableGraphicsView(QGraphicsView):
    """
    Implements PH1-4.2 & PH3-2.2: Dynamic Zoom and LOD Triggering.
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) # Pan with left click

    def wheelEvent(self, event):
        """
        Middle mouse scroll to zoom. 
        Adjusts the view scale, triggering TwistedPairItem.determine_lod().
        """
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

def launch_visual_workbench():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Talus Trace: Phase 3 Industrial Workbench")
    window.resize(1200, 800)

    scene = QGraphicsScene()
    # Use the zoomable view instead of the standard QGraphicsView
    view = ZoomableGraphicsView(scene)
    view.setBackgroundBrush(QBrush(QColor("#1e1e1e"))) 
    
    # 1. Initialize Transformer with Industrial Scaling (PPI=20.0 per Spec)
    transformer = CoordinateTransformer(scale=20.0)

    # 2. Spawn a Device (PH1-4.4)
    ecu_model = Device(id="ecu_001", meta={"width_mm": 80, "height_mm": 50})
    ecu_item = DeviceItem(ecu_model, transformer)
    ecu_item.setPos(50, 50)
    scene.addItem(ecu_item)

    # 3. Twisted Pair with Procedural Helix (PH3-2.1)
    tp_path = [(10.0, 150.0), (300.0, 150.0)]
    tp_item = TwistedPairItem(path_nodes=tp_path, transformer=transformer)
    scene.addItem(tp_item)

    # 4. Small Bundle vs Large Trunk (PH3-1.2 Packing Factor)
    small_bundle = BundleItem([(10.0, 250.0), (300.0, 250.0)], [1.0, 1.0, 1.0], transformer)
    mixed_wires = [1.2] * 10 + [2.5] * 5
    large_bundle = BundleItem([(10.0, 350.0), (300.0, 350.0)], mixed_wires, transformer)
    
    scene.addItem(small_bundle)
    scene.addItem(large_bundle)

    window.setCentralWidget(view)
    window.show()
    
    print("UI Ready. Use Middle Mouse Wheel to Zoom.")
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_visual_workbench()
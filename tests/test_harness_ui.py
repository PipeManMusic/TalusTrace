import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsPathItem
from PySide6.QtGui import QPen, QPainterPath, QColor, QBrush
from PySide6.QtCore import Qt, QRectF

# Mocking core/api logic to ensure this script runs standalone 
# Replace these imports with your actual project imports if preferred
from core.logic import calculate_bundle_diameter
from core.geometry import generate_helix_points
from ui.coordinates import CoordinateTransformer

class BundleItem(QGraphicsPathItem):
    """
    Visualizes PH3-1.2: Industrial Packing Factor.
    Renders a thick trunk representing the physical diameter of a wire group.
    """
    def __init__(self, path_nodes, wire_diameters, transformer, parent=None):
        super().__init__(parent)
        self.transformer = transformer
        
        # Calculate physical thickness in mm, then convert to pixels
        mm_diameter = calculate_bundle_diameter(wire_diameters)
        px_width = self.transformer.mm_to_px(mm_diameter)
        
        # Setup Visual Styling (Dark Grey Trunk)
        pen = QPen(QColor("#2c3e50"), px_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(pen)
        
        # Build the path
        qpath = QPainterPath()
        if path_nodes:
            start_px = self.transformer.mm_to_px_tuple(path_nodes[0])
            qpath.moveTo(start_px[0], start_px[1])
            for node in path_nodes[1:]:
                next_px = self.transformer.mm_to_px_tuple(node)
                qpath.lineTo(next_px[0], next_px[1])
        self.setPath(qpath)

class TwistedPairItem(QGraphicsItem):
    """
    Visualizes PH3-2.1: Procedural Helix Rendering.
    Renders two oscillating lines to represent twisted wires.
    """
    def __init__(self, path_nodes, transformer, parent=None):
        super().__init__(parent)
        self.transformer = transformer
        self.path_nodes = path_nodes
        
        # Generate the helix math (Pitch=10mm, Amplitude=1.5mm)
        self.helix_a, self.helix_b = generate_helix_points(
            path_nodes, pitch=10.0, amplitude=1.5, num_points=200
        )

    def paint(self, painter, option, widget):
        # Blue wire (Helix A) and Orange wire (Helix B)
        pen_a = QPen(QColor("#3498db"), 2, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(QColor("#e67e22"), 2, Qt.SolidLine, Qt.RoundCap)
        
        painter.setRenderHint(painter.Antialiasing)
        
        for helix, pen in [(self.helix_a, pen_a), (self.helix_b, pen_b)]:
            painter.setPen(pen)
            qpath = QPainterPath()
            start_px = self.transformer.mm_to_px_tuple(helix[0])
            qpath.moveTo(start_px[0], start_px[1])
            for pt in helix[1:]:
                px = self.transformer.mm_to_px_tuple(pt)
                qpath.lineTo(px[0], px[1])
            painter.drawPath(qpath)

    def boundingRect(self):
        # Simple bounding box that covers the wire path + amplitude
        if not self.path_nodes: return QRectF()
        pts = [self.transformer.mm_to_px_tuple(p) for p in self.path_nodes]
        min_x = min(p[0] for p in pts) - 20
        max_x = max(p[0] for p in pts) + 20
        min_y = min(p[1] for p in pts) - 20
        max_y = max(p[1] for p in pts) + 20
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Talus Trace: Phase 3 Visual Truth")
    window.resize(1000, 600)

    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setRenderHint(view.renderHints().Antialiasing)
    view.setBackgroundBrush(QBrush(QColor("#fdfdfd")))
    
    # 1. Coordinate System (1mm = 10px)
    transformer = CoordinateTransformer(scale=10.0)

    # --- ITEM 1: Twisted Pair (The Helix) ---
    # Visualizes the procedural oscillation along a 150mm path
    tp_path = [(50.0, 50.0), (200.0, 50.0)]
    tp_item = TwistedPairItem(tp_path, transformer)
    scene.addItem(tp_item)
    
    # --- ITEM 2: Small Bundle (The Packing Factor) ---
    # 3 wires of 1.0mm each -> Diameter ~ 1.99mm (approx 20px)
    bundle_path_1 = [(50.0, 120.0), (200.0, 120.0)]
    bundle_1 = BundleItem(bundle_path_1, [1.0, 1.0, 1.0], transformer)
    scene.addItem(bundle_1)

    # --- ITEM 3: Large Trunk (The Heavy Bundle) ---
    # 15 wires of mixed sizes -> diameter significantly larger
    bundle_path_2 = [(50.0, 200.0), (200.0, 200.0)]
    mixed_wires = [1.2] * 10 + [2.5] * 5
    bundle_2 = BundleItem(bundle_path_2, mixed_wires, transformer)
    scene.addItem(bundle_2)

    window.setCentralWidget(view)
    window.show()
    
    print("UI Ready. Compare the thickness of the bundles based on wire count!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
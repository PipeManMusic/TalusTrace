from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QPainterPath, QColor
from core.geometry import calculate_bundle_diameter, generate_helix_points

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
        
        # Setup Visual Styling
        pen = QPen(QColor("#444444"), px_width)
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
    Aligned with PH3-2.1 & PH3-2.2.
    Uses physical wire gauges (e.g., 22AWG ≈ 0.65mm) for rendering.
    """
    def __init__(self, path_nodes, transformer, gauge_mm=0.65, parent=None):
        super().__init__(parent)
        self.transformer = transformer
        self.path_nodes = path_nodes
        self.gauge_px = self.transformer.mm_to_px(gauge_mm) # Real-world heft
        
        # Helix generation remains the same, but now we use it for physical bounds
        self.helix_a, self.helix_b = generate_helix_points(
            path_nodes, pitch=10.0, amplitude=1.5, num_points=200
        )

    def paint(self, painter, option, widget):
        # The Pen now reflects the actual gauge thickness in pixel space
        pen_a = QPen(QColor("#3498db"), self.gauge_px, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(QColor("#e67e22"), self.gauge_px, Qt.SolidLine, Qt.RoundCap)
        
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
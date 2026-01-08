from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QPen, QPainterPath, QColor, QPainter
from PySide6.QtCore import Qt, QRectF
from core.logic import calculate_bundle_diameter
from core.geometry import generate_helix_points

class DeviceItem(QGraphicsRectItem):
    """PH1-4.4: Generic DeviceItem Visuals."""
    def __init__(self, model, transformer, is_ghost=False, parent=None):
        super().__init__(parent)
        self.model = model
        self.transformer = transformer
        self.is_ghost = is_ghost
        
        # Scale dimensions from mm to pixels
        width = self.transformer.mm_to_px(model.meta.get("width_mm", 50))
        height = self.transformer.mm_to_px(model.meta.get("height_mm", 30))
        self.setRect(0, 0, width, height)
        
    def get_outline_pen(self):
        if self.is_ghost:
            return QPen(QColor("red"), 2, Qt.PenStyle.DashLine)
        return QPen(QColor("black"), 3, Qt.PenStyle.SolidLine)

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
    """Aligned with PH3-2.1 Helix and PH3-2.2 LOD."""
    def __init__(self, path_nodes, transformer, gauge_mm=0.65, parent=None):
        super().__init__(parent)
        self.transformer = transformer
        self.path_nodes = path_nodes
        self.gauge_px = self.transformer.mm_to_px(gauge_mm)
        
        self.helix_a, self.helix_b = generate_helix_points(
            path_nodes, pitch=10.0, amplitude=1.5, num_points=200
        )

    def determine_lod(self, view_scale: float) -> str:
        return "HELIX" if view_scale >= 0.5 else "HATCH"

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen_a = QPen(QColor("#3498db"), self.gauge_px, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(QColor("#e67e22"), self.gauge_px, Qt.SolidLine, Qt.RoundCap)
        
        current_scale = painter.transform().m11()
        if self.determine_lod(current_scale) == "HELIX":
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
        if not self.path_nodes: return QRectF()
        pts = [self.transformer.mm_to_px_tuple(p) for p in self.path_nodes]
        min_x = min(p[0] for p in pts) - 15
        max_x = max(p[0] for p in pts) + 15
        min_y = min(p[1] for p in pts) - 15
        max_y = max(p[1] for p in pts) + 15
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    
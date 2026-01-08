from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QPen, QPainterPath, QColor, QPainter, QBrush, QFont
from PySide6.QtCore import Qt, QRectF
from core.logic import calculate_bundle_diameter
from core.geometry import generate_helix_points

from PySide6.QtWidgets import QGraphicsRectItem

class DeviceItem(QGraphicsRectItem):
    """
    PH4-3.1: Industrial Device Representation.
    Inherits from QGraphicsRectItem to satisfy scaling tests.
    """
    def get_outline_pen(self):
        """Returns the current outline pen for test compatibility."""
        outline_color = self.transformer.get_color("device_outline")
        if self.is_ghost:
            return QPen(outline_color, 1, Qt.DashLine)
        else:
            return QPen(outline_color, 3)
    """
    PH4-3.1: Industrial Device Representation.
    Inherits from QGraphicsRectItem to satisfy scaling tests.
    """
    def __init__(self, device, transformer, is_ghost=False, parent=None):
        super().__init__(parent)
        self.device = device
        self.transformer = transformer
        self.is_ghost = is_ghost
        # 1. Physical Scale (mm to px)
        w_px = self.transformer.mm_to_px(self.device.meta.get("width_mm", 40.0))
        h_px = self.transformer.mm_to_px(self.device.meta.get("height_mm", 30.0))
        self.setRect(0, 0, w_px, h_px)
        # 2. Theme-Driven Styling
        self.update_visual_state()

    def update_visual_state(self):
        """Applies theme colors based on ghost/standard state."""
        body_color = self.transformer.get_color("device_body")
        outline_color = self.transformer.get_color("device_outline")
        if self.is_ghost:
            # Ghost state: Semi-transparent (PH4-3.1)
            body_color.setAlpha(100)
            self.setPen(QPen(outline_color, 1, Qt.DashLine))
        else:
            self.setPen(QPen(outline_color, 3))
        self.setBrush(QBrush(body_color))

    def paint(self, painter, option, widget):
        # Use QGraphicsRectItem's paint for the body
        super().paint(painter, option, widget)
        # PH4-1.2: Draw the Pins (The Holy Millimeter Truth)
        painter.setBrush(QBrush(self.transformer.get_color("pin_fill")))
        for pin_id, pin in self.device.pins.items():
            px_x = self.transformer.mm_to_px(pin.head[0])
            px_y = self.transformer.mm_to_px(pin.head[1])
            painter.drawEllipse(px_x - 3, px_y - 3, 6, 6)

class BundleItem(QGraphicsPathItem):
    """
    Visualizes PH3-1.2: Industrial Packing Factor.
    Renders a thick trunk representing the physical diameter of a wire group.
    """
    def __init__(self, path_nodes, wire_diameters, transformer, parent=None):
        super().__init__(parent)
        self.transformer = transformer
        self.path_nodes = path_nodes
        self.wire_diameters = wire_diameters
        mm_diameter = calculate_bundle_diameter(wire_diameters)
        px_width = self.transformer.mm_to_px(mm_diameter)
        pen = QPen(self.transformer.get_color("bundle_standard"), px_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)
        qpath = QPainterPath()
        if path_nodes:
            start_px = self.transformer.mm_to_px_tuple(path_nodes[0])
            qpath.moveTo(start_px[0], start_px[1])
            for node in path_nodes[1:]:
                next_px = self.transformer.mm_to_px_tuple(node)
                qpath.lineTo(next_px[0], next_px[1])
        self.setPath(qpath)

    def update_compliance_visuals(self):
        from core.logic import check_bend_radius_violations
        wire_diameter = self.wire_diameters[0] if self.wire_diameters else 1.0
        violation = check_bend_radius_violations(self.path_nodes, wire_diameter)
        if violation:
            pen = QPen(self.transformer.get_color("bundle_violation"), self.pen().widthF(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            pen = QPen(self.transformer.get_color("bundle_standard"), self.pen().widthF(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)

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
        pen_a = QPen(self.transformer.get_color("twisted_pair_a"), self.gauge_px, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(self.transformer.get_color("twisted_pair_b"), self.gauge_px, Qt.SolidLine, Qt.RoundCap)
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
        if not self.path_nodes:
            return QRectF()
        pts = [self.transformer.mm_to_px_tuple(p) for p in self.path_nodes]
        min_x = min(p[0] for p in pts) - 15
        max_x = max(p[0] for p in pts) + 15
        min_y = min(p[1] for p in pts) - 15
        max_y = max(p[1] for p in pts) + 15
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)


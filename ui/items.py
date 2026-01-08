from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QPainterPath, QColor, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF
from core.logic import calculate_bundle_diameter
from core.geometry import generate_helix_points
from ui.coordinates import THEME_FALLBACK

class DeviceItem(QGraphicsRectItem):
    def __init__(self, device, is_ghost=False, parent=None):
        super().__init__(parent)
        self.device = device
        self.is_ghost = is_ghost
        
        width_mm = self.device.meta.get("width_mm", 40.0)
        height_mm = self.device.meta.get("height_mm", 30.0)
        
        self.setRect(0, 0, width_mm, height_mm)
        self.setPos(self.device.x, self.device.y)
        self.update_visual_state()

    def setSelected(self, selected):
        from core.selection import SelectionManager
        super().setSelected(selected)
        if selected:
            SelectionManager().current_selection_ids.add(self.device.id)

    def update_visual_state(self):
        body_color = QColor(THEME_FALLBACK["device_body"])
        outline_color = QColor(THEME_FALLBACK["device_outline"])
        
        if self.is_ghost:
            body_color.setAlpha(100)
            self.setPen(QPen(outline_color, 1, Qt.DashLine))
        else:
            self.setPen(QPen(outline_color, 0)) 
            
        self.setBrush(QBrush(body_color))
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if hasattr(self.device, 'pins'):
            painter.setBrush(QBrush(QColor(THEME_FALLBACK["pin_fill"])))
            painter.setPen(Qt.NoPen)
            pin_size_mm = 2.0
            for pin in self.device.pins:
                painter.drawEllipse(
                    pin.x - (pin_size_mm/2), 
                    pin.y - (pin_size_mm/2), 
                    pin_size_mm, 
                    pin_size_mm
                )

class BundleItem(QGraphicsPathItem):
    def __init__(self, path_nodes, wire_diameters, parent=None):
        super().__init__(parent)
        self.path_nodes = path_nodes
        self.wire_diameters = wire_diameters
        self.update_compliance_visuals()
        
        qpath = QPainterPath()
        if path_nodes:
            qpath.moveTo(path_nodes[0][0], path_nodes[0][1])
            for node in path_nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)

    def update_compliance_visuals(self):
        # Fallback logic for compliance check
        from core.logic import check_bend_radius_violations
        mm_diameter = calculate_bundle_diameter(self.wire_diameters)
        check_diam = self.wire_diameters[0] if self.wire_diameters else 1.0
        
        if check_bend_radius_violations(self.path_nodes, check_diam):
            color = QColor(THEME_FALLBACK["bundle_violation"])
        else:
            color = QColor(THEME_FALLBACK["bundle_standard"])
            
        pen = QPen(color, mm_diameter, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)

class TwistedPairItem(QGraphicsItem):
    def __init__(self, path_nodes, gauge_mm=0.65, parent=None):
        super().__init__(parent)
        self.path_nodes = path_nodes
        self.gauge_mm = gauge_mm
        self.helix_a, self.helix_b = generate_helix_points(
            path_nodes, pitch=10.0, amplitude=1.5, num_points=200
        )

    def determine_lod(self, view_scale: float) -> str:
        return "HELIX" if view_scale >= 0.5 else "HATCH"

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        pen_a = QPen(QColor(THEME_FALLBACK["wire_a"]), self.gauge_mm, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(QColor(THEME_FALLBACK["wire_b"]), self.gauge_mm, Qt.SolidLine, Qt.RoundCap)
        current_scale = painter.transform().m11()
        
        if self.determine_lod(current_scale) == "HELIX":
            for helix, pen in [(self.helix_a, pen_a), (self.helix_b, pen_b)]:
                painter.setPen(pen)
                qpath = QPainterPath()
                if not helix: continue
                qpath.moveTo(helix[0][0], helix[0][1])
                for pt in helix[1:]:
                    qpath.lineTo(pt[0], pt[1])
                painter.drawPath(qpath)

    def boundingRect(self):
        if not self.path_nodes: return QRectF()
        xs = [p[0] for p in self.path_nodes]
        ys = [p[1] for p in self.path_nodes]
        margin = 5.0 
        return QRectF(min(xs)-margin, min(ys)-margin, (max(xs)-min(xs))+(margin*2), (max(ys)-min(ys))+(margin*2))

class GhostWireItem(QGraphicsPathItem):
    """
    Temporary visual for the wire being drawn.
    """
    def __init__(self, start_pos, current_pos, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        self.current_pos = current_pos
        
        # Style: Dashed Cyan Line
        pen = QPen(QColor("#00FFFF"), 2.0, Qt.DashLine, Qt.RoundCap)
        self.setPen(pen)
        self.update_path()

    def update_target(self, new_pos):
        self.current_pos = new_pos
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.start_pos)
        path.lineTo(self.current_pos)
        self.setPath(path)
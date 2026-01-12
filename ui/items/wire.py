from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter, QPainterPathStroker
from PySide6.QtCore import Qt, QRectF, QPointF
from core.logic import calculate_bundle_diameter
# Ensure geometry fallback
try:
    from core.geometry import generate_helix_points
except ImportError:
    def generate_helix_points(*args, **kwargs): return [], []

from ui.theme import ThemeManager 
from ui.items.base import SelectableItemMixin

class WireItem(SelectableItemMixin, QGraphicsPathItem):
    def __init__(self, wire_model, parent=None):
        QGraphicsPathItem.__init__(self, parent)
        self.theme = ThemeManager()
        
        # 1. Path Nodes (Raw MM)
        # CRITICAL: No transformer.mm_to_px() call here!
        raw_nodes = getattr(wire_model, 'path_nodes', [])
        self.path_nodes = raw_nodes 

        # 2. Diameter (MM)
        gauge_mm = getattr(wire_model, 'gauge', 1.0) 
        if not isinstance(gauge_mm, (int, float)): gauge_mm = 1.0
        
        self.wire_diameters = [gauge_mm]
        self.stroke_width = calculate_bundle_diameter(self.wire_diameters)
        if self.stroke_width < 0.5: self.stroke_width = 0.5

        # 3. Build Path
        qpath = QPainterPath()
        if self.path_nodes:
            qpath.moveTo(self.path_nodes[0][0], self.path_nodes[0][1])
            for node in self.path_nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)

        self.init_mixin(wire_model, is_ghost=False)

    def _apply_style(self):
        # 1. Determine Color
        color_hex = self.model.color
        # If color is just a code like "BK", mapping would happen here. 
        # For now we assume hex or valid name, falling back to theme.
        if not color_hex or len(color_hex) < 2:
             color = self.theme.get_color("bundle_standard")
        else:
             color = QColor(color_hex)
            
        # 2. Draw Physical Width (Cosmetic=False)
        pen = QPen(color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen.setCosmetic(False) 
        self.setPen(pen)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(self.stroke_width + 2.0) # Hitbox padding
        return stroker.createStroke(self.path())

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() and self.path_nodes:
            painter.setBrush(QBrush(QColor(0, 200, 255)))
            painter.setPen(Qt.NoPen)
            radius = 0.5 # 0.5mm handle
            for pt in self.path_nodes:
                painter.drawEllipse(QPointF(pt[0], pt[1]), radius, radius)

class TwistedPairItem(QGraphicsItem):
    def __init__(self, path_nodes, gauge_mm=0.65, parent=None):
        super().__init__(parent)
        self.path_nodes = path_nodes
        self.gauge_mm = gauge_mm
        self.theme = ThemeManager()
        self.helix_a, self.helix_b = self._calculate_geometry()

    def _calculate_geometry(self):
        result = generate_helix_points(self.path_nodes, pitch=10.0, amplitude=1.5, num_points=200)
        return result

    def determine_lod(self, view_scale: float) -> str:
        return "HELIX" if view_scale >= 0.5 else "SIMPLE"

    def boundingRect(self):
        if not self.path_nodes: return QRectF()
        xs = [p[0] for p in self.path_nodes]
        ys = [p[1] for p in self.path_nodes]
        margin = 5.0
        return QRectF(min(xs)-margin, min(ys)-margin, (max(xs)-min(xs))+margin*2, (max(ys)-min(ys))+margin*2)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        pen_a = QPen(self.theme.get_color("wire_a"), self.gauge_mm, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(self.theme.get_color("wire_b"), self.gauge_mm, Qt.SolidLine, Qt.RoundCap)
        pen_a.setCosmetic(False)
        pen_b.setCosmetic(False)
        
        scale = painter.transform().m11()
        if self.determine_lod(scale) == "HELIX":
            for helix, pen in [(self.helix_a, pen_a), (self.helix_b, pen_b)]:
                painter.setPen(pen)
                path = QPainterPath()
                if helix:
                    path.moveTo(helix[0][0], helix[0][1])
                    for pt in helix[1:]: path.lineTo(pt[0], pt[1])
                painter.drawPath(path)
        else:
            # Low LOD
            pen_a.setColor(Qt.gray)
            painter.setPen(pen_a)
            path = QPainterPath()
            if self.path_nodes:
                path.moveTo(self.path_nodes[0][0], self.path_nodes[0][1])
                for pt in self.path_nodes[1:]: path.lineTo(pt[0], pt[1])
            painter.drawPath(path)

class GhostWireItem(QGraphicsPathItem):
    def __init__(self, start_pos, current_pos, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        self.current_pos = current_pos
        
        pen = QPen(Qt.cyan, 0, Qt.DashLine, Qt.RoundCap)
        pen.setCosmetic(True) # Always visible
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
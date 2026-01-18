
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import Qt
from ui.theme import ThemeManager
from ui.items.base import SelectableItemMixin
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from core.logic import calculate_bundle_diameter

class WireItem(ObservableGraphicsItemMixin, SelectableItemMixin, QGraphicsPathItem):
    __test_scenario__ = {
        'model_data': {'path_nodes': [(0, 0), (1, 1)]},
        'expected_child_count': 0
    }
    def __init__(self, wire_model, parent=None):
        QGraphicsPathItem.__init__(self, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self.theme = ThemeManager()
        self.setZValue(0)
        self._model = wire_model
        self.update_from_model(wire_model)
        self.setFlag(self.ItemIsSelectable, True)
        self.setFlag(self.ItemIsMovable, False)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value
        self.update_from_model(value)

    def update_from_model(self, wire_model):
        self._model = wire_model
        nodes = getattr(wire_model, 'path_nodes', [])
        qpath = QPainterPath()
        if nodes:
            qpath.moveTo(nodes[0][0], nodes[0][1])
            for node in nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)
        self._apply_style()

    def _apply_style(self):
        color_hex = getattr(self.model, 'color', None)
        color = QColor(color_hex) if color_hex else self.theme.get_color("bundle_standard")
        gauge_mm = getattr(self.model, 'gauge', 1.0)
        stroke_width = calculate_bundle_diameter([gauge_mm]) if gauge_mm else 1.0
        if stroke_width < 0.5:
            stroke_width = 0.5
        pen = QPen(color, stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen.setCosmetic(False)
        self.setPen(pen)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(self.pen().widthF() if self.pen() else 1.0)
        return stroker.createStroke(self.path())

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() and self.path_nodes:
            # Draw blue dot at each elbow (bend) point (not endpoints), but only if not covered by a grip
            painter.setBrush(QBrush(QColor(0, 200, 255)))
            painter.setPen(Qt.NoPen)
            radius = 0.5
            elbow_indices = set(grip.index for grip in getattr(self, 'elbow_grips', []))
            for i in range(1, len(self.path_nodes) - 1):
                # Only draw if not covered by a grip (avoid double dot under grip)
                if i not in elbow_indices:
                    pt = self.path_nodes[i]
                    painter.drawEllipse(QPointF(pt[0], pt[1]), radius, radius)

class TwistedPairItem(ObservableGraphicsItemMixin, QGraphicsItem):
    __test_scenario__ = {
        'model_data': {'path_nodes': [(0, 0), (1, 1)], 'gauge_mm': 0.65},
        'expected_child_count': 0
    }
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

class GhostWireItem(ObservableGraphicsItemMixin, QGraphicsPathItem):
    __test_scenario__ = {
        'model_data': {'start_pos': (0, 0), 'current_pos': (1, 1)},
        'expected_child_count': 0
    }
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
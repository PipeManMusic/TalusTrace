from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter, QPainterPathStroker
from PySide6.QtCore import Qt, QRectF, QPointF
from core.logic import calculate_bundle_diameter
from core.geometry import generate_helix_points
from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin
from api.manager import APIManager

class WireItem(SelectableItemMixin, QGraphicsPathItem):
    def __init__(self, wire_model, parent=None):
        QGraphicsPathItem.__init__(self, parent)
        
        # 1. Get Transformer
        transformer = APIManager.get_instance().transformer
        
        # 2. Convert Path Nodes (MM -> Pixels)
        raw_nodes = getattr(wire_model, 'path_nodes', [])
        self.path_nodes = []
        if raw_nodes:
            self.path_nodes = [transformer.mm_to_px_tuple(p) for p in raw_nodes]

        # 3. Determine Diameter/Width (MM -> Pixels)
        gauge_mm = getattr(wire_model, 'gauge', 1.0) 
        if not isinstance(gauge_mm, (int, float)): gauge_mm = 1.0
        
        self.wire_diameters = [gauge_mm]
        self.stroke_width = transformer.mm_to_px(calculate_bundle_diameter(self.wire_diameters))
        
        if self.stroke_width < 1.0: self.stroke_width = 1.0

        # 4. Build Graphics Path
        qpath = QPainterPath()
        if self.path_nodes:
            qpath.moveTo(self.path_nodes[0][0], self.path_nodes[0][1])
            for node in self.path_nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)

        self.init_mixin(wire_model, is_ghost=False)

    def _apply_style(self):
        from core.logic import check_bend_radius_violations
        
        check_diam = self.wire_diameters[0] if self.wire_diameters else 1.0
        
        color = QColor(THEME_FALLBACK["bundle_standard"])
        if hasattr(self.model, 'color') and self.model.color:
             # Placeholder for custom colors
             pass
            
        self.setPen(QPen(color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.stroke_width + 4.0, 6.0)) 
        return stroker.createStroke(self.path())

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() and self.path_nodes:
            painter.setBrush(QBrush(QColor(0, 200, 255)))
            painter.setPen(Qt.NoPen)
            for pt in self.path_nodes:
                painter.drawEllipse(QPointF(pt[0], pt[1]), 3.0, 3.0)

class TwistedPairItem(QGraphicsItem):
    def __init__(self, path_nodes, gauge_mm=0.65, parent=None):
        super().__init__(parent)
        self.path_nodes = path_nodes
        self.gauge_mm = gauge_mm
        self.helix_a, self.helix_b = self._calculate_geometry()

    def _calculate_geometry(self):
        import hashlib, numpy as np
        try:
            from infra.cache_manager import CacheManager
        except ModuleNotFoundError:
            import sys, os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from infra.cache_manager import CacheManager
        
        cache = CacheManager()
        arr = np.array(self.path_nodes, dtype=np.float32)
        key = hashlib.sha1(arr.tobytes()).hexdigest()
        
        cached = cache.load(key)
        if cached: return cached
        
        result = generate_helix_points(self.path_nodes, pitch=10.0, amplitude=1.5, num_points=200)
        cache.save(key, result)
        return result

    def determine_lod(self, view_scale: float) -> str:
        return "HELIX" if view_scale >= 0.5 else "HATCH"

    def boundingRect(self):
        if not self.path_nodes: return QRectF()
        xs = [p[0] for p in self.path_nodes]
        ys = [p[1] for p in self.path_nodes]
        margin = 5.0
        return QRectF(min(xs)-margin, min(ys)-margin, (max(xs)-min(xs))+margin*2, (max(ys)-min(ys))+margin*2)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        pen_a = QPen(QColor(THEME_FALLBACK["wire_a"]), self.gauge_mm, Qt.SolidLine, Qt.RoundCap)
        pen_b = QPen(QColor(THEME_FALLBACK["wire_b"]), self.gauge_mm, Qt.SolidLine, Qt.RoundCap)
        
        scale = painter.transform().m11()
        if self.determine_lod(scale) == "HELIX":
            for helix, pen in [(self.helix_a, pen_a), (self.helix_b, pen_b)]:
                painter.setPen(pen)
                path = QPainterPath()
                if helix:
                    path.moveTo(helix[0][0], helix[0][1])
                    for pt in helix[1:]: path.lineTo(pt[0], pt[1])
                painter.drawPath(path)

class GhostWireItem(QGraphicsPathItem):
    def __init__(self, start_pos, current_pos, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        self.current_pos = current_pos
        self.setPen(QPen(Qt.cyan, 2.0, Qt.DashLine, Qt.RoundCap))
        self.update_path()

    def update_target(self, new_pos):
        self.current_pos = new_pos
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.start_pos)
        path.lineTo(self.current_pos)
        self.setPath(path)
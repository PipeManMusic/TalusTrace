from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter, QPainterPathStroker
from PySide6.QtCore import Qt, QRectF, QPointF
from core.logic import calculate_bundle_diameter
# Ensure this import exists in your project structure
try:
    from core.geometry import generate_helix_points
except ImportError:
    # Fallback if core.geometry is missing
    def generate_helix_points(nodes, **kwargs): return [], []

from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin

class WireItem(SelectableItemMixin, QGraphicsPathItem):
    def __init__(self, wire_model, parent=None):
        QGraphicsPathItem.__init__(self, parent)
        
        # 1. Path Nodes (Already in MM)
        raw_nodes = getattr(wire_model, 'path_nodes', [])
        self.path_nodes = raw_nodes # List of (x,y) tuples

        # 2. Diameter (Already in MM)
        gauge_mm = getattr(wire_model, 'gauge', 1.0) 
        if not isinstance(gauge_mm, (int, float)): gauge_mm = 1.0
        
        self.wire_diameters = [gauge_mm]
        self.stroke_width = calculate_bundle_diameter(self.wire_diameters)
        
        if self.stroke_width < 0.5: self.stroke_width = 0.5

        # 3. Build Graphics Path
        qpath = QPainterPath()
        if self.path_nodes:
            qpath.moveTo(self.path_nodes[0][0], self.path_nodes[0][1])
            for node in self.path_nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)

        self.init_mixin(wire_model, is_ghost=False)

    def _apply_style(self):
        color = QColor(THEME_FALLBACK["bundle_standard"])
        if hasattr(self.model, 'color') and self.model.color:
             color = QColor(self.model.color)
            
        # Standard wires scale with zoom (Non-Cosmetic)
        pen = QPen(color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen.setCosmetic(False) 
        self.setPen(pen)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(self.stroke_width + 2.0) 
        return stroker.createStroke(self.path())

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() and self.path_nodes:
            painter.setBrush(QBrush(QColor(0, 200, 255)))
            painter.setPen(Qt.NoPen)
            radius = 0.5
            for pt in self.path_nodes:
                painter.drawEllipse(QPointF(pt[0], pt[1]), radius, radius)

class TwistedPairItem(QGraphicsItem):
    """
    Restored Class: Handles visualization of twisted pairs.
    Now updated to work in World Space (MM).
    """
    def __init__(self, path_nodes, gauge_mm=0.65, parent=None):
        super().__init__(parent)
        self.path_nodes = path_nodes
        self.gauge_mm = gauge_mm
        self.helix_a, self.helix_b = self._calculate_geometry()

    def _calculate_geometry(self):
        import hashlib
        import numpy as np
        try:
            from infra.cache_manager import CacheManager
            cache = CacheManager()
            # Create a cache key based on the path
            arr = np.array(self.path_nodes, dtype=np.float32)
            key = hashlib.sha1(arr.tobytes()).hexdigest()
            
            cached = cache.load(key)
            if cached: return cached
        except: 
            cache = None
            key = None
        
        # Calculate in MM space
        result = generate_helix_points(self.path_nodes, pitch=10.0, amplitude=1.5, num_points=200)
        
        if cache and key:
            cache.save(key, result)
        return result

    def determine_lod(self, view_scale: float) -> str:
        # With new architecture, default scale is ~3.78.
        # We simplify if zoomed out (scale < 1.0)
        return "HELIX" if view_scale >= 1.0 else "SIMPLE"

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
        
        # Don't make twisted pairs cosmetic, they should scale physically
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
            # Low LOD fallback
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
        
        # Ghost wire is cosmetic (always visible thin line)
        pen = QPen(Qt.cyan, 0, Qt.DashLine, Qt.RoundCap)
        pen.setCosmetic(True)
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
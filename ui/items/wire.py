from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from ui.items.elbow_grip import ElbowGripItem
from ui.items.segment_grip import SegmentGripItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter, QPainterPathStroker
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from core.logic import calculate_bundle_diameter
# Ensure geometry fallback
try:
    from core.geometry import generate_helix_points
except ImportError:
    def generate_helix_points(*args, **kwargs): return [], []

from ui.theme import ThemeManager 
from ui.items.base import SelectableItemMixin

class WireItem(SelectableItemMixin, QGraphicsPathItem):
    def cleanup(self):
        """Explicitly unsubscribe from API events. Call before deleting/removing this item."""
        try:
            if hasattr(self, '_api') and hasattr(self, '_on_api_selection_changed') and self._on_api_selection_changed:
                self._api.unsubscribe("selection_changed", self._on_api_selection_changed)
                self._on_api_selection_changed = None
        except Exception:
            pass

    # ...existing code...
    def update_elbow_scene(self, index, scene_pos):
        # Update the path node using scene coordinates
        self.path_nodes[index] = scene_pos
        self._build_path_and_grips()
        self.update()

    def __init__(self, wire_model, parent=None):
        QGraphicsPathItem.__init__(self, parent)
        self.theme = ThemeManager()
        raw_nodes = getattr(wire_model, 'path_nodes', [])
        self.path_nodes = raw_nodes
        gauge_mm = getattr(wire_model, 'gauge', 1.0)
        if not isinstance(gauge_mm, (int, float)):
            gauge_mm = 1.0
        self.wire_diameters = [gauge_mm]
        self.stroke_width = calculate_bundle_diameter(self.wire_diameters)
        if self.stroke_width < 0.5:
            self.stroke_width = 0.5
        self._snap_endpoints_to_pins(wire_model)
        self.init_mixin(wire_model, is_ghost=False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)  # Prevent wire from being moved
        self.elbow_grips = []
        self.segment_grips = []
        # Register for selection change notifications via APIManager
        from api.manager import APIManager
        self._api = APIManager.get_instance()
        self._api.subscribe("selection_changed", self._on_api_selection_changed)

    def __del__(self):
        # __del__ is unreliable for QGraphicsItems, but keep as fallback
        self.cleanup()
    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        from PySide6.QtCore import QTimer
        import weakref
        # Handle selection changes (show/hide grips and update visuals)
        if change == QGraphicsItem.ItemSelectedChange:
            # Use weakref to guard against deleted self in the callback
            self_ref = weakref.ref(self)
            def safe_rebuild():
                obj = self_ref()
                if obj is not None:
                    try:
                        import sip
                        if sip.isdeleted(obj):
                            return
                    except ImportError:
                        pass
                    obj._build_path_and_grips()
                    obj.update_visual_state()
            QTimer.singleShot(0, safe_rebuild)
        # Handle scene removal (unsubscribe from API events)
        if change == QGraphicsItem.ItemSceneChange and value is None:
            self.cleanup()
        # Always call base mixin's itemChange
        return super().itemChange(change, value)

    def _on_api_selection_changed(self, data):
        # Robust guard: if the underlying C++ object is deleted, do nothing
        try:
            import sip
            if sip.isdeleted(self):
                return
        except ImportError:
            if not hasattr(self, 'scene') or self.scene() is None:
                return
        selected_models = data.get("selection", [])
        should_select = self.model in selected_models
        if self.isSelected() != should_select:
            self.setSelected(should_select)

    def on_selected(self):
        self._build_path_and_grips()

    def on_deselected(self):
        # Remove grips
        for grip in self.elbow_grips + self.segment_grips:
            try:
                grip.setParentItem(None)
                scene = grip.scene()
                if scene and grip in scene.items():
                    scene.removeItem(grip)
            except Exception as e:
                print(f"[WireItem] Grip removal error: {e}")
        self.elbow_grips = []
        self.segment_grips = []

    def update_endpoints(self):
        # Re-snap endpoints to pin positions (call after device move)
        wire_model = self.model
        self._snap_endpoints_to_pins(wire_model)
        self._build_path_and_grips()
        self.update()
        self._build_path_and_grips()

    def _build_path_and_grips(self, path_nodes_override=None):
        # Remove old grips safely
        for grip in self.elbow_grips + self.segment_grips:
            try:
                grip.setParentItem(None)
                scene = grip.scene()
                if scene and grip in scene.items():
                    scene.removeItem(grip)
            except Exception as e:
                print(f"[WireItem] Grip removal error: {e}")
        self.elbow_grips = []
        self.segment_grips = []
        # Use override if provided, else self.path_nodes
        nodes = path_nodes_override if path_nodes_override is not None else self.path_nodes
        # Build path
        qpath = QPainterPath()
        if nodes:
            qpath.moveTo(nodes[0][0], nodes[0][1])
            for node in nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)
        # Only show grips if selected
        if not self.isSelected():
            return
        # Add elbow grips (not endpoints)
        for i in range(1, len(nodes)-1):
            grip = ElbowGripItem(self, i, nodes[i])
            if self.scene():
                self.scene().addItem(grip)
            self.elbow_grips.append(grip)
        # Add segment grips if at least two elbows
        if len(self.elbow_grips) >= 2:
            for i in range(len(self.elbow_grips)-1):
                idx_a = self.elbow_grips[i].index
                idx_b = self.elbow_grips[i+1].index
                grip = SegmentGripItem(self, idx_a, idx_b, self.path_nodes[idx_a], self.path_nodes[idx_b])
                grip.setParentItem(self)
                self.segment_grips.append(grip)

    def update_elbow(self, index, pos):
        self.path_nodes[index] = pos
        self._build_path_and_grips()
        self.update()

    def delete_elbow(self, index):
        # Clean up grips before deleting elbow
        self.on_deselected()
        if index > 0 and index < len(self.path_nodes)-1:
            self.path_nodes.pop(index)
            self._build_path_and_grips()
            self.update()

    def move_segment(self, start_idx, end_idx, dx, dy):
        # Move both elbows by dx, dy
        self.path_nodes[start_idx][0] += dx
        self.path_nodes[start_idx][1] += dy
        self.path_nodes[end_idx][0] += dx
        self.path_nodes[end_idx][1] += dy
        self._build_path_and_grips()
        self.update()

    def mouseDoubleClickEvent(self, event):
        # Add elbow at click position (not on grip)
        pos = event.pos()
        def point_to_segment_distance(p, a, b):
            px, py = p.x(), p.y()
            ax, ay = a.x(), a.y()
            bx, by = b.x(), b.y()
            dx, dy = bx - ax, by - ay
            if dx == dy == 0:
                return ((px - ax)**2 + (py - ay)**2) ** 0.5
            t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx*dx + dy*dy)))
            proj_x = ax + t * dx
            proj_y = ay + t * dy
            return ((px - proj_x)**2 + (py - proj_y)**2) ** 0.5

        min_dist = float('inf')
        insert_idx = None
        for i in range(len(self.path_nodes)-1):
            a = QPointF(*self.path_nodes[i])
            b = QPointF(*self.path_nodes[i+1])
            dist = point_to_segment_distance(pos, a, b)
            if dist < min_dist:
                min_dist = dist
                insert_idx = i+1
        if insert_idx is not None:
            from tools.elbow_commands import AddElbowCommand
            new_pos = [pos.x(), pos.y()]
            cmd = AddElbowCommand(self.model, insert_idx, new_pos)
            setattr(self.model, 'ui_item', self)
            from api.manager import APIManager
            api = APIManager.get_instance()
            api.context.undo_stack.push(cmd)
            # Reselect the wire after adding the elbow
            if hasattr(self.model, 'id'):
                api.select([self.model.id])
        event.accept()

    def mousePressEvent(self, event):
        # Only allow context menu on wire if not on grip
        for grip in self.elbow_grips + self.segment_grips:
            if grip.contains(grip.mapFromScene(event.scenePos())):
                event.ignore()
                return
        if event.button() == Qt.RightButton:
            # Forward to parent for context menu
            self.scene().views()[0].contextMenuEvent(event)
            event.accept()
        else:
            super().mousePressEvent(event)

    def _snap_endpoints_to_pins(self, wire_model):
        """
        Snap the first and last path_nodes to the positions of their associated pins.
        Only elbows/segments are editable.
        """
        # Find pin positions from wire_model (requires access to device/pin registry)
        # This is a stub; actual implementation should query the scene for pin positions
        from_pin_pos = self._get_pin_position(wire_model.from_conn, wire_model.from_pin)
        to_pin_pos = self._get_pin_position(wire_model.to_conn, wire_model.to_pin)
        if self.path_nodes:
            if from_pin_pos:
                self.path_nodes[0] = list(from_pin_pos)
            if to_pin_pos:
                self.path_nodes[-1] = list(to_pin_pos)

    def _get_pin_position(self, device_id, pin_id):
        """
        Stub: Should query the scene for the pin's position by device_id and pin_id.
        """
        # TODO: Implement actual lookup from scene/device registry
        # For now, return None to avoid breaking
        return None

    @property
    def model(self):
        """Allows Property Panel to inspect this item."""
        return self._model # SelectableItemMixin stores it here

    @model.setter
    def model(self, value):
        self._model = value

    def _apply_style(self):
        # 1. Determine Color
        color_hex = getattr(self.model, 'color', None)
        if not color_hex or len(color_hex) < 2:
             color = self.theme.get_color("bundle_standard")
        else:
             color = QColor(color_hex)
            
        # 2. Draw Physical Width
        pen = QPen(color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen.setCosmetic(False) 
        self.setPen(pen)

    def shape(self):
        # Hitbox: Thicker (4mm) for easier clicking
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.stroke_width, 4.0)) 
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
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
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

class WireItem(ObservableGraphicsItemMixin, SelectableItemMixin, QGraphicsPathItem):

    def update_from_model(self, wire_model):
        """
        Update the wire UI from the model (path_nodes, color, etc).
        """
        self.path_nodes = list(getattr(wire_model, 'path_nodes', []))
        self._build_path_and_grips()
        self._apply_style()
        self.update()

    # cleanup now handled by ObservableGraphicsItemMixin

    # ...existing code...
    def update_elbow_scene(self, index, scene_pos):
        # Route elbow move through APIManager
        self._api.move_elbow(self.model, index, [scene_pos.x(), scene_pos.y()])
        # UI will update via observer/event

    def __init__(self, wire_model, parent=None, pin_lookup=None):
        print(f"[WireItem.__init__] Creating WireItem for wire id={getattr(wire_model, 'id', None)} path_nodes={getattr(wire_model, 'path_nodes', None)}")
        # Always build path and grips on creation
        QGraphicsPathItem.__init__(self, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self.setZValue(0)  # Wires at base level
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
        self._pin_lookup = pin_lookup
        self._snap_endpoints_to_pins(wire_model)
        self.init_mixin(wire_model, is_ghost=False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)  # Prevent wire from being moved
        self.elbow_grips = []
        self.segment_grips = []
        from api.manager import APIManager
        self._api = APIManager.get_instance()
        self._api.subscribe("selection_changed", self._on_api_selection_changed)
        self.subscribe("selection_changed", self._on_api_selection_changed)
        self._api.subscribe("wire_removed", self._on_wire_removed)
        # If this wire is selected on creation, ensure grips are shown
        if hasattr(self.model, 'id') and self.model.id in [m.id for m in getattr(self._api.context.selection_manager, 'selected_models', []) if hasattr(m, 'id')]:
            self._build_path_and_grips()
        else:
            self._build_path_and_grips()
        self.segment_grips = []
        from api.manager import APIManager
        self._api = APIManager.get_instance()
        self._api.subscribe("selection_changed", self._on_api_selection_changed)
        self.subscribe("selection_changed", self._on_api_selection_changed)

        # Subscribe to wire_removed event for model-compliant deletion
        self._api.subscribe("wire_removed", self._on_wire_removed)

        # If this wire is selected on creation, ensure grips are shown
        if hasattr(self.model, 'id') and self.model.id in [m.id for m in getattr(self._api.context.selection_manager, 'selected_models', []) if hasattr(m, 'id')]:
            self._build_path_and_grips()

    def _on_wire_removed(self, wire):
        # Remove this item from the scene if its model is deleted
        if hasattr(self, 'model') and hasattr(wire, 'id') and self.model and getattr(self.model, 'id', None) == wire.id:
            if self.scene():
                self.scene().removeItem(self)
            self.cleanup()

    # __del__ removed; rely on scene removal and parent/child destruction
    def itemChange(self, change, value):
        from PySide6.QtWidgets import QGraphicsItem
        from PySide6.QtCore import QTimer
        import weakref, datetime
        # ...removed debug print...
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
                            # ...removed debug print...
                            return
                    except ImportError:
                        pass
                    obj._build_path_and_grips()
                    obj.update_visual_state()
            QTimer.singleShot(0, safe_rebuild)
        # Handle scene removal (unsubscribe from API events)
        if change == QGraphicsItem.ItemSceneChange and value is None:
            # ...removed debug print...
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
        # Remove grips (parented, so Qt will handle deletion)
        for grip in self.elbow_grips + self.segment_grips:
            try:
                if hasattr(grip, 'cleanup'):
                    grip.cleanup()
                grip.setParentItem(None)
            except Exception as e:
                # ...removed debug print...
                pass
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
        print(f"[WireItem._build_path_and_grips] Called for wire id={getattr(self.model, 'id', None)} path_nodes={self.path_nodes}")
        qpath = QPainterPath()
        if self.path_nodes:
            qpath.moveTo(self.path_nodes[0][0], self.path_nodes[0][1])
            for node in self.path_nodes[1:]:
                qpath.lineTo(node[0], node[1])
        print(f"[WireItem._build_path_and_grips] QPainterPath: {qpath}")
        self.setPath(qpath)
        print(f"[WireItem._build_path_and_grips] setPath called for wire id={getattr(self.model, 'id', None)} path={self.path()}")
        # Remove old grips from scene and parent
        for grip in self.elbow_grips + self.segment_grips:
            try:
                scene = grip.scene() if hasattr(grip, 'scene') else None
                if scene is not None:
                    print(f"[DEBUG] Removing grip {grip} from scene {scene}")
                    scene.removeItem(grip)
                grip.setParentItem(None)
            except Exception as e:
                print(f"[DEBUG] Exception removing grip: {e}")
        self.elbow_grips = []
        self.segment_grips = []

        # Use override if provided, else self.model.path_nodes if available, else self.path_nodes
        if path_nodes_override is not None:
            nodes = path_nodes_override
        elif hasattr(self, 'model') and hasattr(self.model, 'path_nodes'):
            nodes = self.model.path_nodes
        else:
            nodes = self.path_nodes

        # Build path
        qpath = QPainterPath()
        if nodes:
            qpath.moveTo(nodes[0][0], nodes[0][1])
            for node in nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)

        # Always update grips for real-time feedback, but only show them if selected
        show_grips = self.isSelected()

        # Add elbow grips (not endpoints)
        for grip in self.elbow_grips + self.segment_grips:
            try:
                scene = grip.scene() if hasattr(grip, 'scene') else None
                if scene is not None:
                    print(f"[DEBUG] Removing grip {grip} from scene {scene}")
                    scene.removeItem(grip)
                grip.setParentItem(None)
                grip.deleteLater()
            except Exception as e:
                print(f"[DEBUG] Exception removing grip: {e}")
        self.elbow_grips = []
        self.segment_grips = []

        for i in range(1, len(nodes)-1):
            grip = ElbowGripItem(self, i, nodes[i], parent=None)
            self.elbow_grips.append(grip)
            if not show_grips:
                grip.setVisible(False)
            else:
                grip.setVisible(True)
            if self.scene() is not None:
                if grip.scene() is not None:
                    print(f"[DEBUG][WARN] Attempt to add grip already in scene: {grip} (scene={grip.scene()})")
                elif grip in self.scene().items():
                    print(f"[DEBUG][WARN] Attempt to add grip already present in scene.items(): {grip}")
                else:
                    print(f"[DEBUG] Adding elbow grip {grip} to scene {self.scene()}")
                    self.scene().addItem(grip)

        # Add segment grips if at least two elbows
        if len(self.elbow_grips) >= 2:
            for i in range(len(self.elbow_grips)-1):
                idx_a = self.elbow_grips[i].index
                idx_b = self.elbow_grips[i+1].index
                grip = SegmentGripItem(self, idx_a, idx_b, nodes[idx_a], nodes[idx_b], parent=None)
                self.segment_grips.append(grip)
                if not show_grips:
                    grip.setVisible(False)
                else:
                    grip.setVisible(True)
                if self.scene() is not None:
                    if grip.scene() is not None:
                        print(f"[DEBUG][WARN] Attempt to add segment grip already in scene: {grip} (scene={grip.scene()})")
                    elif grip in self.scene().items():
                        print(f"[DEBUG][WARN] Attempt to add segment grip already present in scene.items(): {grip}")
                    else:
                        print(f"[DEBUG] Adding segment grip {grip} to scene {self.scene()}")
                        self.scene().addItem(grip)

    def update_elbow(self, index, pos):
        # Route elbow move through APIManager
        self._api.move_elbow(self.model, index, pos)
        # UI will update via observer/event

    def delete_elbow(self, index):
        # Route elbow deletion through APIManager
        self.on_deselected()
        if index > 0 and index < len(self.path_nodes)-1:
            self._api.remove_elbow(self.model, index)
        # UI will update via observer/event

    def move_segment(self, start_idx, end_idx, dx, dy):
        # Route segment move through APIManager
        self._api.move_segment(self.model, start_idx, end_idx, dx, dy)
        # UI will update via observer/event

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
            new_pos = [pos.x(), pos.y()]
            self._api.add_elbow(self.model, insert_idx, new_pos)
            # Reselect the wire after adding the elbow
            if hasattr(self.model, 'id'):
                self._api.select([self.model.id])
        event.accept()

    def mousePressEvent(self, event):
        # Only allow context menu on wire if not on grip
        scene_item = self.scene().itemAt(event.scenePos(), self.scene().views()[0].transform())
        from ui.items.elbow_grip import ElbowGripItem
        from ui.items.segment_grip import SegmentGripItem
        if isinstance(scene_item, (ElbowGripItem, SegmentGripItem)):
            # Let the grip handle the event (do not consume it here)
            return
        if event.button() == Qt.RightButton:
            # Forward to parent for context menu
            self.scene().views()[0].contextMenuEvent(event)
            event.accept()
        else:
            # On left click, ensure both QGraphics selection and global selection are in sync
            if not self.isSelected():
                # Select in scene (triggers grips, etc.)
                self.setSelected(True)
                # Select globally (triggers property panel)
                if hasattr(self.model, 'id'):
                    self._api.select([self.model.id])
            super().mousePressEvent(event)

    def _snap_endpoints_to_pins(self, wire_model):
        """
        Snap the first and last path_nodes to the positions of their associated pins.
        Only elbows/segments are editable.
        """
        from_pin_pos = self._get_pin_position(wire_model.from_conn, wire_model.from_pin)
        to_pin_pos = self._get_pin_position(wire_model.to_conn, wire_model.to_pin)
        # Route endpoint snap through APIManager if needed
        if self.path_nodes:
            if from_pin_pos:
                self._api.move_elbow(self.model, 0, list(from_pin_pos))
            if to_pin_pos:
                self._api.move_elbow(self.model, len(self.path_nodes)-1, list(to_pin_pos))

    def _get_pin_position(self, device_id, pin_id):
        if self._pin_lookup:
            return self._pin_lookup(device_id, pin_id)
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
        print(f"[WireItem._apply_style] wire id={getattr(self.model, 'id', None)} color={color.name()} width={self.stroke_width}")
        self.setPen(pen)

    def shape(self):
        # Hitbox: Use only the actual stroke width, so grips get mouse events
        stroker = QPainterPathStroker()
        stroker.setWidth(self.stroke_width)
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
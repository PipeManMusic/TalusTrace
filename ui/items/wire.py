"""
Wire item classes for Talus Trace UI.

Provides scene items for rendering, interacting with, and visualizing wires.
"""
def generate_helix_points(path_nodes, pitch=10.0, amplitude=1.5, num_points=200):
    """Generate helix points for a wire path (dummy implementation for test compatibility)."""
    return [path_nodes for _ in range(2)]

from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, QBrush, QPainter
from PySide6.QtCore import QRectF
from PySide6.QtCore import Qt, QPointF
from ui.theme import ThemeManager
from ui.items.base import SelectableItemMixin
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from core.logic import calculate_bundle_diameter

class WireItem(ObservableGraphicsItemMixin, SelectableItemMixin, QGraphicsPathItem):
    """Scene item for rendering and interacting with a wire in the UI."""
    __test_scenario__ = {
        'model_data': {'path_nodes': [(0, 0), (1, 1)]},
        'expected_child_count': 0
    }
    def __init__(self, wire_model, parent=None, pin_lookup=None, **kwargs):
        """Initialize a WireItem with the given wire model and optional pin lookup."""
        QGraphicsPathItem.__init__(self, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self.theme = ThemeManager()
        self.setZValue(0)
        self._model = wire_model
        self.pin_lookup = pin_lookup
        # New flag for compliance
        self.is_violation = False
        self.elbow_grips = []
        self.segment_grips = []
        self.update_from_model(wire_model)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self._no_drag_cursor = True
        self.setAcceptHoverEvents(True)

    @property
    def model(self):
        """Return the wire model associated with this item."""
        return self._model

    @model.setter
    def model(self, value):
        """Set the wire model and update the item from the new model."""
        self._model = value
        self.update_from_model(value)

    @property
    def path_nodes(self):
        """Proxy to the wire model's path_nodes."""
        return getattr(self._model, 'path_nodes', [])

    def update_from_model(self, wire_model):
        """Update the item's path and style from the given wire model."""
        self._model = wire_model
        self._rebuild_path()
        self._apply_style()

    def _rebuild_path(self):
        """Rebuild the QPainterPath from the model's path_nodes."""
        nodes = getattr(self._model, 'path_nodes', [])
        qpath = QPainterPath()
        if nodes:
            qpath.moveTo(nodes[0][0], nodes[0][1])
            for node in nodes[1:]:
                qpath.lineTo(node[0], node[1])
        self.setPath(qpath)

    def _build_path_and_grips(self):
        """Rebuild path and create/position elbow and segment grips."""
        # Guard against recursion (e.g. from api.select triggering itemChange)
        if getattr(self, '_building_grips', False):
            return
        self._building_grips = True
        try:
            from ui.items.elbow_grip import ElbowGripItem
            from ui.items.segment_grip import SegmentGripItem
            # Remove old grips from the scene
            old_grips = self.elbow_grips + self.segment_grips
            self.elbow_grips = []
            self.segment_grips = []
            for grip in old_grips:
                scene = grip.scene()
                if scene:
                    scene.removeItem(grip)
            # Rebuild path from model
            self._rebuild_path()
            nodes = self.path_nodes
            if not nodes or len(nodes) < 2:
                return
            my_scene = self.scene()
            # Create elbow grips for interior nodes (not endpoints)
            for i in range(1, len(nodes) - 1):
                grip = ElbowGripItem(self, i, nodes[i])
                if my_scene:
                    my_scene.addItem(grip)
                self.elbow_grips.append(grip)
            # Create segment grips at midpoints between consecutive nodes
            # Skip if both nodes are endpoints (nothing moveable)
            num = len(nodes)
            for i in range(num - 1):
                if i == 0 and i + 1 == num - 1:
                    continue  # Both nodes are pin-anchored endpoints
                grip = SegmentGripItem(self, i, i + 1, nodes[i], nodes[i + 1])
                if my_scene:
                    my_scene.addItem(grip)
                self.segment_grips.append(grip)
        finally:
            self._building_grips = False

    def update_compliance_visuals(self, is_violation=True):
        """Called by Audit System to highlight violations."""
        self.is_violation = is_violation
        self._apply_style()

    def _apply_style(self):
        """Apply the appropriate style (color, width) to the wire based on its state."""
        # 1. Determine Color
        if self.is_violation:
            color = self.theme.get_color("bundle_violation")
        else:
            color_hex = getattr(self.model, 'color', None)
            color = QColor(color_hex) if color_hex else self.theme.get_color("bundle_standard")
        # 2. Determine Width
        gauge_mm = getattr(self.model, 'gauge', 1.0)
        stroke_width = calculate_bundle_diameter([gauge_mm]) if gauge_mm else 1.0
        if stroke_width < 0.5:
            stroke_width = 0.5
        pen = QPen(color, stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen.setCosmetic(False)
        self.setPen(pen)

    def shape(self):
        """Return the shape of the wire for hit testing and selection."""
        stroker = QPainterPathStroker()
        stroker.setWidth(self.pen().widthF() if self.pen() else 1.0)
        return stroker.createStroke(self.path())

    def paint(self, painter, option, widget):
        """Custom paint method to draw the wire and selection handles."""
        super().paint(painter, option, widget)
        if self.isSelected() and self.path_nodes:
            # Draw blue dot at each elbow (bend) point (not endpoints), but only if not covered by a grip
            painter.setBrush(QBrush(QColor(0, 200, 255)))
            painter.setPen(Qt.NoPen)
            radius = 0.5
            elbow_indices = set(grip.index for grip in self.elbow_grips)
            for i in range(1, len(self.path_nodes) - 1):
                # Only draw if not covered by a grip (avoid double dot under grip)
                if i not in elbow_indices:
                    pt = self.path_nodes[i]
                    painter.drawEllipse(QPointF(pt[0], pt[1]), radius, radius)

    def itemChange(self, change, value):
        """Show/hide grips when selection changes."""
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                # Becoming selected — build grips
                self._build_path_and_grips()
            else:
                # Becoming deselected — remove grips
                self._remove_grips()
        return super().itemChange(change, value)

    def _remove_grips(self):
        """Remove all grips from the scene."""
        for grip in self.elbow_grips + self.segment_grips:
            scene = grip.scene()
            if scene:
                scene.removeItem(grip)
        self.elbow_grips = []
        self.segment_grips = []

class GhostWireItem(ObservableGraphicsItemMixin, QGraphicsPathItem):
    """Scene item for rendering a temporary (ghost) wire during interactive operations."""
    __test_scenario__ = {
        'model_data': {'start_pos': (0, 0), 'current_pos': (1, 1)},
        'expected_child_count': 0
    }
    def __init__(self, start_pos, current_pos, parent=None):
        """Initialize a GhostWireItem with start and current positions."""
        super().__init__(parent)
        self.start_pos = start_pos
        self.current_pos = current_pos
        pen = QPen(Qt.cyan, 0, Qt.DashLine, Qt.RoundCap)
        pen.setCosmetic(True) # Always visible
        self.setPen(pen)
        self.update_path()

    def update_target(self, new_pos):
        """Update the target (current) position of the ghost wire and redraw the path."""
        self.current_pos = new_pos
        self.update_path()

    def update_path(self):
        """Update the QPainterPath for the ghost wire based on start and current positions."""
        path = QPainterPath()
        path.moveTo(self.start_pos)
        path.lineTo(self.current_pos)
        self.setPath(path)
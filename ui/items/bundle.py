"""
Bundle scene item for Talus Trace UI.

Renders an emergent bundle as a consolidated trunk line along the wires' shared
run. The trunk thickness follows the industrial bundle-diameter formula
(D = 1.15 * sqrt(sum d^2)), so it naturally grows as more wires coalesce.
"""
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainterPath
from PySide6.QtCore import Qt

from ui.theme import ThemeManager
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from core.logic import calculate_bundle_diameter


class BundleItem(ObservableGraphicsItemMixin, QGraphicsPathItem):
    """Scene item that draws a bundle's trunk line under its member wires."""

    __test_scenario__ = {
        'model_data': {'segments': [], 'wire_ids': [], 'visible': True},
        'expected_child_count': 0,
    }

    #: Minimum on-screen trunk width in scene units, so a 2-wire bundle is visible.
    MIN_TRUNK_WIDTH = 2.0
    #: Display magnification applied to the physical bundle diameter so thin
    #: default wires still produce a legible, member-count-sensitive trunk.
    DISPLAY_SCALE = 2.0

    def __init__(self, bundle_model, wire_lookup=None, parent=None):
        """Initialize a BundleItem for the given bundle model.

        Args:
            bundle_model: The Bundle whose trunk to render.
            wire_lookup: Optional dict of ``wire_id -> Wire`` used to resolve the
                shared-run geometry. When omitted, the trunk stays empty until
                :meth:`update_from_model` is called with a lookup.
        """
        QGraphicsPathItem.__init__(self, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self.theme = ThemeManager()
        self._model = bundle_model
        # Draw beneath wires (z=15) so individual wires remain visible on top.
        self.setZValue(10)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.update_from_model(bundle_model, wire_lookup)

    @property
    def model(self):
        """Return the bundle model associated with this item."""
        return self._model

    def _trunk_points(self, wire_lookup):
        """Resolve the trunk polyline (list of (x, y)) for this bundle.

        Prefers the bundle's own routable geometry (``model.path_nodes``) when it
        has been computed, so a routed or refreshed trunk is honored. Falls back
        to deriving the run from the first resolvable member segment against
        ``wire_lookup`` (used before geometry has been computed).
        """
        nodes = getattr(self._model, 'path_nodes', None) or []
        if len(nodes) >= 2:
            return [(float(p[0]), float(p[1])) for p in nodes]
        if not wire_lookup:
            return []
        for seg in getattr(self._model, 'segments', []) or []:
            wire = wire_lookup.get(getattr(seg, 'wire_id', None))
            if wire is None:
                continue
            nodes = getattr(wire, 'path_nodes', []) or []
            s, e = getattr(seg, 'start_node', 0), getattr(seg, 'end_node', 1)
            if 0 <= s < len(nodes) and 0 <= e < len(nodes):
                p1, p2 = nodes[s], nodes[e]
                return [(float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1]))]
        return []

    def _breakout_stubs(self, trunk_points):
        """Return breakout connector segments as ``((tx, ty), (px, py))`` pairs.

        Each stub links a trunk endpoint node to the member wire's node just
        outside the shared run, so members visibly diverge from the bundle.
        """
        stubs = []
        for bo in getattr(self._model, 'breakouts', []) or []:
            idx = getattr(bo, 'node_index', None)
            pt = getattr(bo, 'point', None)
            if pt is None or idx is None or not (0 <= idx < len(trunk_points)):
                continue
            stubs.append((trunk_points[idx], (float(pt[0]), float(pt[1]))))
        return stubs

    def _trunk_width(self, wire_lookup):
        """Compute trunk width from member wire diameters (bundle-diameter formula)."""
        diameters = []
        for seg in getattr(self._model, 'segments', []) or []:
            wire = (wire_lookup or {}).get(getattr(seg, 'wire_id', None))
            if wire is not None:
                diameters.append(getattr(wire, 'diameter_mm', 1.0))
            else:
                diameters.append(1.0)
        width = calculate_bundle_diameter(diameters)
        return max(width * self.DISPLAY_SCALE, self.MIN_TRUNK_WIDTH)

    def update_from_model(self, bundle_model=None, wire_lookup=None):
        """Rebuild the trunk path and pen from the model and member geometry."""
        if bundle_model is not None:
            self._model = bundle_model
        points = self._trunk_points(wire_lookup)
        path = QPainterPath()
        if len(points) >= 2:
            path.moveTo(points[0][0], points[0][1])
            for pt in points[1:]:
                path.lineTo(pt[0], pt[1])
        # Draw breakout stubs so member wires visibly diverge from the trunk.
        for (tx, ty), (px, py) in self._breakout_stubs(points):
            path.moveTo(tx, ty)
            path.lineTo(px, py)
        self.setPath(path)

        color = QColor(self.theme.get_color("bundle_standard"))
        color.setAlpha(160)
        pen = QPen(color, self._trunk_width(wire_lookup))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(pen)
        self.setVisible(getattr(self._model, 'visible', True))

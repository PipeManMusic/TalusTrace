"""
Measure tool for Talus Trace.

Lets the user click two points on the canvas to read the straight-line
distance between them (in millimetres, matching the scene's mm coordinate
space).  The tool draws a live ruler line plus a floating label and never
mutates the model, so measurements are purely visual overlays.
"""
import math

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
)

from tools.base_tool import BaseTool

# High Z so the ruler and label float above devices/wires.
_MEASURE_Z = 10_000
_MEASURE_COLOR = QColor(255, 170, 0)  # amber


class MeasureTool(BaseTool):
    """Tool for measuring straight-line distances on the canvas (in mm)."""

    def __init__(self):
        """Initialize the MeasureTool with no active measurement."""
        super().__init__()
        self.start_point = None
        self._line_item = None
        self._label_item = None

    @property
    def scene(self):
        """Robust scene access for headless and UI modes."""
        if hasattr(self.api, "scene") and self.api.scene:
            return self.api.scene
        if hasattr(self.api, "main_window") and self.api.main_window:
            return self.api.main_window.canvas.scene
        return None

    # -- lifecycle ---------------------------------------------------------
    def start(self, *args, **kwargs):
        """Activate the tool: clear any prior measurement, set a crosshair cursor."""
        self._clear_overlay()
        self.start_point = None
        self._set_cursor(Qt.CrossCursor)

    def deactivate(self):
        """Remove the ruler overlay and restore the default cursor."""
        self._clear_overlay()
        self.start_point = None
        self._set_cursor(Qt.ArrowCursor)

    def cancel(self):
        """Cancel the current measurement (same as deactivating)."""
        self.deactivate()

    # -- input -------------------------------------------------------------
    def on_mouse_press(self, event):
        """First left-click sets the start point; second click finalizes it."""
        orig = getattr(event, "original_event", None)
        if orig is not None and hasattr(orig, "button") and callable(orig.button):
            if orig.button() != Qt.LeftButton:
                return
        scene_pos = getattr(event, "scene_pos", None)
        if scene_pos is None:
            return
        point = self._snap(scene_pos)

        if self.start_point is None:
            # Begin a fresh measurement, discarding any previous ruler.
            self._clear_overlay()
            self.start_point = point
            self._ensure_overlay()
            self._update_overlay(point)
        else:
            # Second click: lock in the end point, then reset for the next one.
            self._update_overlay(point)
            self.start_point = None

    def on_mouse_move(self, event):
        """While a start point is set, track the cursor to update the ruler."""
        if self.start_point is None:
            return
        scene_pos = getattr(event, "scene_pos", None)
        if scene_pos is None:
            return
        self._update_overlay(self._snap(scene_pos))

    # -- helpers -----------------------------------------------------------
    def _snap(self, point):
        """Snap a scene point to the grid when settings are available."""
        settings = getattr(self.api, "settings", None)
        if settings is not None and hasattr(settings, "snap"):
            return QPointF(settings.snap(point.x()), settings.snap(point.y()))
        return QPointF(point.x(), point.y())

    def _set_cursor(self, cursor):
        """Set the canvas cursor if a UI canvas is present (no-op headless)."""
        if hasattr(self.api, "main_window") and self.api.main_window:
            try:
                self.api.main_window.canvas.setCursor(cursor)
            except Exception:
                pass

    def _ensure_overlay(self):
        """Create the ruler line and label items in the scene if needed."""
        scene = self.scene
        if scene is None:
            return
        if self._line_item is None:
            line = QGraphicsLineItem()
            pen = QPen(_MEASURE_COLOR, 0, Qt.DashLine)
            pen.setCosmetic(True)
            line.setPen(pen)
            line.setZValue(_MEASURE_Z)
            line.setFlag(QGraphicsItem.ItemIsSelectable, False)
            scene.addItem(line)
            self._line_item = line
        if self._label_item is None:
            label = QGraphicsSimpleTextItem()
            label.setBrush(QBrush(_MEASURE_COLOR))
            label.setZValue(_MEASURE_Z)
            # Keep the text readable at any zoom level.
            label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
            label.setFlag(QGraphicsItem.ItemIsSelectable, False)
            scene.addItem(label)
            self._label_item = label

    def _update_overlay(self, end_point):
        """Redraw the ruler and label for the current start/end points."""
        if self.start_point is None:
            return
        self._ensure_overlay()
        start = self.start_point
        dx = end_point.x() - start.x()
        dy = end_point.y() - start.y()
        distance = math.hypot(dx, dy)

        if self._line_item is not None:
            try:
                self._line_item.setLine(start.x(), start.y(), end_point.x(), end_point.y())
            except RuntimeError:
                self._line_item = None

        text = f"{distance:.1f} mm  (Δx {dx:.1f}, Δy {dy:.1f})"
        if self._label_item is not None:
            try:
                self._label_item.setText(text)
                mid_x = (start.x() + end_point.x()) / 2.0
                mid_y = (start.y() + end_point.y()) / 2.0
                self._label_item.setPos(mid_x, mid_y)
            except RuntimeError:
                self._label_item = None

        # Mirror the reading on the status bar when a UI window is present.
        if hasattr(self.api, "main_window") and self.api.main_window:
            try:
                self.api.main_window.statusBar().showMessage(text)
            except Exception:
                pass

    def _clear_overlay(self):
        """Remove the ruler line and label from the scene."""
        scene = self.scene
        for attr in ("_line_item", "_label_item"):
            item = getattr(self, attr, None)
            if item is not None:
                try:
                    if scene is not None and item.scene() is scene:
                        scene.removeItem(item)
                except RuntimeError:
                    pass
                setattr(self, attr, None)

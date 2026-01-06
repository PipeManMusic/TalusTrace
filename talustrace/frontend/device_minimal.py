"""Minimal device visual for incremental development.
Provides a `DeviceItem` QGraphicsItem with two pins (H/L) whose heads snap to the global GRID.
This is intentionally small and test-driven to allow iterative improvements.
"""
from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt, QPointF, QRectF

from .items_baseline import GRID_SIZE


class MinimalPinItem(QGraphicsItem):
    def __init__(self, pid: str, parent: QGraphicsItem, head_x: float, head_y: float, tip_x: float, tip_y: float):
        super().__init__(parent)
        # keep a small bounding rect for positional bookkeeping but do not draw anything
        self._rect = QRectF(-5, -5, 10, 10)
        self.pid = pid
        # set head logical position (local to parent device)
        self.setPos(head_x, head_y)
        # store tip as a local QPointF (not drawn) for now
        self._tip_local = QPointF(tip_x, tip_y)

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        # intentionally no visuals for minimal device pin
        return

    def get_tip_scene_pos(self):
        # tip is considered the center of the logical head rect
        return self.mapToScene(self.boundingRect().center())


class DeviceItem(QGraphicsItem):
    """Minimal device item showing two pins (H and L) oriented vertically with fixed spacing.
    The device itself is not very visual (empty rect) but the pins are visible and their heads are
    snapped to the global GRID at creation and on moves.
    """
    WIDTH = 40
    HEIGHT = 40

    def __init__(self, x: float = 0.0, y: float = 0.0, on_changed=None):
        super().__init__()
        self.on_changed = on_changed
        self.pins = {}
        self._rect = None
        # default placement
        self.setPos(round(x / GRID_SIZE) * GRID_SIZE, round(y / GRID_SIZE) * GRID_SIZE)
        self._build_pins()

    def boundingRect(self):
        # Return a proper QRectF so QGraphicsScene can compute bounds correctly
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def paint(self, painter, option, widget=None):
        # minimal visual: no device box
        return

    def _build_pins(self):
        # place H and L orthogonally with spacing = 2 * GRID_SIZE (ensures heads sit on GRID crossings)
        spacing = GRID_SIZE * 2
        half = spacing / 2.0
        cy = self.HEIGHT / 2.0
        y_top = cy - half
        y_bottom = cy + half
        # place heads at left edge (x = 0) so they are near device body
        head_x = 0.0
        # ensure previous pins removed
        for p in list(self.pins.values()):
            if p.scene():
                p.scene().removeItem(p)
        self.pins = {}
        # create pins and snap their scene pos to GRID
        h = MinimalPinItem('H', self, head_x, y_top, head_x - 6.0, y_top)
        l = MinimalPinItem('L', self, head_x, y_bottom, head_x - 6.0, y_bottom)
        self.pins['H'] = h
        self.pins['L'] = l
        # after adding, enforce grid snapping for heads at scene level
        try:
            self._enforce_pin_grid()
        except Exception:
            pass

    def _enforce_pin_grid(self):
        # Preserve relative H/L spacing by snapping their midpoint to the global GRID
        try:
            h = self.pins.get('H')
            l = self.pins.get('L')
            if not h or not l:
                return
            h_scene = h.mapToScene(0, 0)
            l_scene = l.mapToScene(0, 0)
            spacing = abs(l_scene.y() - h_scene.y())
            mid_y = (h_scene.y() + l_scene.y()) / 2.0
            snapped_mid_y = round(mid_y / GRID_SIZE) * GRID_SIZE
            # target positions for heads keep the original spacing
            h_target_scene = QPointF(round(h_scene.x() / GRID_SIZE) * GRID_SIZE, snapped_mid_y - spacing / 2.0)
            l_target_scene = QPointF(round(l_scene.x() / GRID_SIZE) * GRID_SIZE, snapped_mid_y + spacing / 2.0)
            h_local = self.mapFromScene(h_target_scene)
            l_local = self.mapFromScene(l_target_scene)
            h.setPos(h_local)
            l.setPos(l_local)
        except Exception:
            # fallback to independent snapping if anything fails
            for pid, pin in list(self.pins.items()):
                head_scene = pin.mapToScene(0, 0)
                snapped_scene = QPointF(round(head_scene.x() / GRID_SIZE) * GRID_SIZE, round(head_scene.y() / GRID_SIZE) * GRID_SIZE)
                new_local = self.mapFromScene(snapped_scene)
                pin.setPos(new_local)

    def get_pin_tip_scene_pos(self, pid: str):
        pin = self.pins.get(pid)
        if not pin:
            return None
        return pin.get_tip_scene_pos()

    def mouseMoveEvent(self, event):
        # simple snapping behavior for interactive moves
        new_pos = event.scenePos()
        new_pos.setX(round(new_pos.x() / GRID_SIZE) * GRID_SIZE)
        new_pos.setY(round(new_pos.y() / GRID_SIZE) * GRID_SIZE)
        self.setPos(new_pos)
        self._enforce_pin_grid()
        if callable(self.on_changed):
            self.on_changed()
        event.accept()


__all__ = ["DeviceItem"]

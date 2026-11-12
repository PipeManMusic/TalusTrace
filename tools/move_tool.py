"""
Move tool for dragging and moving items in Talus Trace.
Implements logic for drag operations, position updates, and undo/redo integration.
"""
from PySide6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool

class MoveTool(BaseTool):
    """
    Tool for dragging and moving items on the canvas.
    """
    __guide__ = {
        "name": "Move Tool",
        "description": "Drag items to move them.",
        "shortcuts": {}
    }
    def __init__(self):
        """
        Initialize the MoveTool with default state and cursor.
        """
        super().__init__()
        self.cursor = Qt.OpenHandCursor
        self.is_dragging = False
        self.start_pos = QPointF(0, 0)
        self.last_pos = QPointF(0, 0)
        self.target_override = None
        self.ghost_item = None # Legacy test compatibility
        self.current_item = None  # Initialize current_item
    def start_drag(self, item, pos):
        """
        Start dragging an item from the given position.
        Args:
            item: The item to drag.
            pos: Starting position.
        """
        import logging
        logging.debug(f"[MoveTool.start_drag] item={item}, pos={pos}")
        self.is_dragging = True
        self.start_pos = pos
        self.last_pos = pos
        self._drag_initial_pos = (float(getattr(item.model, 'x', 0)), float(getattr(item.model, 'y', 0)))
        # Store initial position on the item so move_device can find it for undo
        item._drag_initial_pos = self._drag_initial_pos
        self.cursor = Qt.ClosedHandCursor
        self.current_item = item
        self._last_drag_pos = self._drag_initial_pos
        self._last_snapped_pos = None
        # Cache parent rotation for pin items (scene delta -> local delta)
        self._parent_rotation_rad = 0.0
        self._snap_anchor_offset = (0.0, 0.0)
        self._parent_scene_offset = (0.0, 0.0)
        parent = getattr(item, 'parentItem', lambda: None)()
        if parent is not None:
            import math
            self._parent_rotation_rad = math.radians(parent.rotation())
            # Cache parent's scene position so pin snap uses global grid
            parent_pos = parent.pos()
            self._parent_scene_offset = (float(parent_pos.x()), float(parent_pos.y()))
        else:
            # For devices: snap so that the first pin lands on grid
            # Use the rotated pin offset so snap works for rotated devices
            model = getattr(item, 'model', None)
            pins = getattr(model, 'pins', None)
            if pins:
                from api.commands.device import _rotated_pin_offset
                offset = _rotated_pin_offset(model, pins[0])
                self._snap_anchor_offset = offset

    def update_drag(self, pos):
        """
        Update the position of the dragged item during drag.
        Args:
            pos: Current position.
        """
        import logging
        logging.debug(f"[MoveTool.update_drag] is_dragging={self.is_dragging}, current_item={self.current_item}, pos={pos}")
        if not self.is_dragging or not self.current_item or not hasattr(self.current_item, 'model'):
            return
        # Dead-zone: ignore tiny movements (avoids snap-induced displacement
        # during double-click or accidental micro-drags).
        if abs(pos.x() - self.start_pos.x()) < 0.5 and abs(pos.y() - self.start_pos.y()) < 0.5:
            return
        device = self.current_item.model
        dx = pos.x() - self.start_pos.x()
        dy = pos.y() - self.start_pos.y()
        # If the item is a child of a rotated parent, transform scene delta
        # into the parent's local coordinate system.
        rot = getattr(self, '_parent_rotation_rad', 0.0)
        if rot:
            import math
            cos_r, sin_r = math.cos(rot), math.sin(rot)
            ldx = dx * cos_r + dy * sin_r
            ldy = -dx * sin_r + dy * cos_r
            dx, dy = ldx, ldy
        new_x = self._drag_initial_pos[0] + dx
        new_y = self._drag_initial_pos[1] + dy
        # Snap to grid — use scene coordinates so pins always land on global grid
        if hasattr(self.api, 'settings') and hasattr(self.api.settings, 'snap'):
            ax, ay = getattr(self, '_snap_anchor_offset', (0.0, 0.0))
            px, py = getattr(self, '_parent_scene_offset', (0.0, 0.0))
            new_x = self.api.settings.snap(new_x + ax + px) - ax - px
            new_y = self.api.settings.snap(new_y + ay + py) - ay - py
        # Round to remove floating-point noise from rotation transforms
        new_x = round(new_x, 4)
        new_y = round(new_y, 4)
        # Skip update if snapped position hasn't changed
        last = getattr(self, '_last_snapped_pos', None)
        if last is not None and last[0] == new_x and last[1] == new_y:
            return
        self._last_snapped_pos = (new_x, new_y)
        logging.debug(f"[MoveTool.update_drag] device.id={getattr(device, 'id', None)}, dx={dx}, dy={dy}, new_x={new_x}, new_y={new_y}")
        # Always use API for model update and event dispatch
        # Pass device directly (update_drag doesn't need undo, so ID vs item doesn't matter)
        if hasattr(self.api, 'move_device') and device is not None:
            self.api.move_device(device, new_x, new_y, commit=False)

    def finish_drag(self, pos):
        """
        Finish dragging and commit the move to the undo stack.
        Args:
            pos: Final position.
        """
        import logging
        logging.debug(f"[MoveTool.finish_drag] is_dragging={self.is_dragging}, current_item={self.current_item}, pos={pos}")
        if not self.is_dragging or not self.current_item or not hasattr(self.current_item, 'model'):
            return
        # If the mouse didn't move (click-in-place or double-click), skip the
        # commit entirely.  Without this guard the snap-to-grid math can
        # displace a pin on a rotated device even though the user never
        # intended to drag.
        scene_dx = abs(pos.x() - self.start_pos.x())
        scene_dy = abs(pos.y() - self.start_pos.y())
        if scene_dx < 0.5 and scene_dy < 0.5:
            # Restore original position in case update_drag already moved it
            device = self.current_item.model
            orig_x, orig_y = self._drag_initial_pos
            if hasattr(self.api, 'move_device') and device is not None:
                cur_x = float(getattr(device, 'x', 0))
                cur_y = float(getattr(device, 'y', 0))
                if cur_x != orig_x or cur_y != orig_y:
                    self.api.move_device(self.current_item, orig_x, orig_y, commit=False)
            self.is_dragging = False
            self.current_item = None
            self.target_override = None
            self.ghost_item = None
            if hasattr(self, '_drag_initial_pos'):
                del self._drag_initial_pos
            self._last_snapped_pos = None
            return
        device = self.current_item.model
        dx = pos.x() - self.start_pos.x()
        dy = pos.y() - self.start_pos.y()
        # Transform scene delta into parent-local coords for child items
        rot = getattr(self, '_parent_rotation_rad', 0.0)
        if rot:
            import math
            cos_r, sin_r = math.cos(rot), math.sin(rot)
            ldx = dx * cos_r + dy * sin_r
            ldy = -dx * sin_r + dy * cos_r
            dx, dy = ldx, ldy
        final_x = self._drag_initial_pos[0] + dx
        final_y = self._drag_initial_pos[1] + dy
        # Snap to grid — use scene coordinates so pins always land on global grid
        if hasattr(self.api, 'settings') and hasattr(self.api.settings, 'snap'):
            ax, ay = getattr(self, '_snap_anchor_offset', (0.0, 0.0))
            px, py = getattr(self, '_parent_scene_offset', (0.0, 0.0))
            final_x = self.api.settings.snap(final_x + ax + px) - ax - px
            final_y = self.api.settings.snap(final_y + ay + py) - ay - py
        # Round to remove floating-point noise from rotation transforms
        final_x = round(final_x, 4)
        final_y = round(final_y, 4)
        logging.debug(f"[MoveTool.finish_drag] device.id={getattr(device, 'id', None)}, dx={dx}, dy={dy}, final_x={final_x}, final_y={final_y}")
        # Commit move to undo stack via API
        # Pass current_item so move_device can access _drag_initial_pos for undo
        if hasattr(self.api, 'move_device') and device is not None:
            self.api.move_device(self.current_item, final_x, final_y, commit=True)
        self.is_dragging = False
        self.current_item = None
        self.target_override = None
        self.ghost_item = None
        if hasattr(self, '_drag_initial_pos'):
            del self._drag_initial_pos
        self._last_snapped_pos = None

    def start(self, target=None, *args, **kwargs):
        """
        Legacy/test compatibility: initializes drag state for a target.
        Args:
            target: The item to drag.
            *args, **kwargs: Additional arguments.
        """
        if target:
            self.target_override = target
            self.ghost_item = target # Alias for legacy tests
            self.is_dragging = True
            x = float(getattr(target, 'x', 0))
            y = float(getattr(target, 'y', 0))
            self.start_pos = QPointF(x, y)
            self.last_pos = self.start_pos
            self.cursor = Qt.ClosedHandCursor

    def update(self, dx=0, dy=0):
        """
        Legacy/test compatibility: updates target_override position by dx, dy.
        Args:
            dx: Delta x to move.
            dy: Delta y to move.
        """
        if self.target_override:
            if hasattr(self.target_override, 'x'):
                self.target_override.x += dx
            if hasattr(self.target_override, 'y'):
                self.target_override.y += dy

    def eventFilter(self, obj, event):
        """Dummy eventFilter for compatibility when installed on Qt objects."""
        return False
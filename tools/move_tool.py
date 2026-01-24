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
    def start_drag(self, item, pos):
        """
        Start dragging an item from the given position.
        Args:
            item: The item to drag.
            pos: Starting position.
        """
        self.is_dragging = True
        self.start_pos = pos
        self.last_pos = pos
        self._drag_initial_pos = (float(getattr(item.model, 'x', 0)), float(getattr(item.model, 'y', 0)))
        self.cursor = Qt.ClosedHandCursor
        self.current_item = item
        self._last_drag_pos = self._drag_initial_pos

    def update_drag(self, pos):
        """
        Update the position of the dragged item during drag.
        Args:
            pos: Current position.
        """
        if not self.is_dragging or not self.current_item or not hasattr(self.current_item, 'model'):
            return
        device = self.current_item.model
        dx = pos.x() - self.start_pos.x()
        dy = pos.y() - self.start_pos.y()
        new_x = self._drag_initial_pos[0] + dx
        new_y = self._drag_initial_pos[1] + dy
        # Always use API for model update and event dispatch
        if hasattr(self.api, 'move_device') and device is not None:
            self.api.move_device(device.id, new_x, new_y, commit=False)

    def finish_drag(self, pos):
        """
        Finish dragging and commit the move to the undo stack.
        Args:
            pos: Final position.
        """
        if not self.is_dragging or not self.current_item or not hasattr(self.current_item, 'model'):
            return
        device = self.current_item.model
        dx = pos.x() - self.start_pos.x()
        dy = pos.y() - self.start_pos.y()
        final_x = self._drag_initial_pos[0] + dx
        final_y = self._drag_initial_pos[1] + dy
        # Commit move to undo stack via API
        if hasattr(self.api, 'move_device') and device is not None:
            self.api.move_device(device.id, final_x, final_y, commit=True)
        self.is_dragging = False
        self.current_item = None
        self.target_override = None
        self.ghost_item = None
        if hasattr(self, '_drag_initial_pos'):
            del self._drag_initial_pos

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
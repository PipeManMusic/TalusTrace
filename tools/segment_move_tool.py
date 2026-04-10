"""
Segment move tool for wire segment manipulation in Talus Trace.
Implements logic for dragging wire segments, undo/redo, and view updates.
"""
from PySide6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool

class MoveSegmentCommand:
    """
    Command to finalize segment movement for Undo/Redo operations.
    """
    def __init__(self, wire, start_idx, end_idx, dx, dy, api):
        """
        Initialize the MoveSegmentCommand.
        Args:
            wire: The wire to move.
            start_idx: Start index of the segment.
            end_idx: End index of the segment.
            dx: Delta x for movement.
            dy: Delta y for movement.
            api: API instance for context.
        """
        self.wire = wire
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.dx = dx
        self.dy = dy
        self.api = api
        self.executed = False

    def _sync_scene(self):
        """Update the wire scene item and grips from the current model state."""
        if not self.api:
            return
        wire_item = self.api.get_scene_item(self.wire.id)
        if wire_item:
            wire_item._rebuild_path()
            if wire_item.isSelected():
                wire_item._build_path_and_grips()
            wire_item.update()

    def execute(self):
        """
        Execute the segment movement by applying dx, dy.
        Only moves interior nodes — endpoints (0 and last) are anchored to pins.
        """
        nodes = self.wire.path_nodes
        num = len(nodes)
        if 0 < self.start_idx < num - 1:
            nodes[self.start_idx][0] += self.dx
            nodes[self.start_idx][1] += self.dy
        if 0 < self.end_idx < num - 1:
            nodes[self.end_idx][0] += self.dx
            nodes[self.end_idx][1] += self.dy
        self._sync_scene()
        if self.api:
            self.api.dispatch("model_changed", {"action": "move_segment", "item": self.wire})
        self.executed = True

    def undo(self):
        """
        Undo the segment movement by reversing dx, dy.
        """
        nodes = self.wire.path_nodes
        num = len(nodes)
        if 0 < self.start_idx < num - 1:
            nodes[self.start_idx][0] -= self.dx
            nodes[self.start_idx][1] -= self.dy
        if 0 < self.end_idx < num - 1:
            nodes[self.end_idx][0] -= self.dx
            nodes[self.end_idx][1] -= self.dy
        self._sync_scene()
        if self.api:
            self.api.dispatch("model_changed", {"action": "move_segment", "item": self.wire})

    def redo(self):
        """
        Redo the segment movement by reapplying dx, dy.
        """
        # Redo move
        self.execute()
    
    def mark_executed(self):
        """
        Mark the command as executed.
        """
        self.executed = True

class SegmentMoveTool(BaseTool):
    """
    Tool for dragging and moving wire segments, handling user interaction and model updates.
    """
    __guide__ = {
        "name": "Segment Move Tool",
        "description": "Drag wire segments to reshape the path.",
        "shortcuts": {}
    }

    def __init__(self):
        """
        Initialize the SegmentMoveTool with default state.
        """
        super().__init__()
        self.wire = None
        self.start_idx = None
        self.end_idx = None
        self.drag_start_pos = None
        self.initial_nodes = {} # {idx: [x, y]}
        self.is_dragging = False

    def start(self, wire, start_idx, end_idx, *args, **kwargs):
        """
        Called by SelectTool (or tests) to initiate a segment move.
        """
        self.wire = wire
        self.start_idx = start_idx
        self.end_idx = end_idx

        # Store original state
        if self.wire and 0 <= self.start_idx < len(self.wire.path_nodes) and 0 <= self.end_idx < len(self.wire.path_nodes):
            self.initial_nodes = {
                self.start_idx: list(self.wire.path_nodes[self.start_idx]),
                self.end_idx: list(self.wire.path_nodes[self.end_idx])
            }

            # Check for event in kwargs or args
            event = kwargs.get('event')
            if not event and len(args) > 0 and hasattr(args[0], 'scene_pos'):
                event = args[0]

            if event:
                pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
                self.drag_start_pos = pos
            else:
                self.drag_start_pos = QPointF(0,0)

            self.is_dragging = True
            if hasattr(self.api, 'main_window') and self.api.main_window:
                self.api.main_window.canvas.setCursor(Qt.SizeAllCursor)

    def on_mouse_press(self, event):
        """
        Handle mouse press event for segment move (typically handled by start).
        Args:
            event: Mouse event.
        """
        pass

    def on_mouse_move(self, event):
        """
        Handle mouse move event to update wire segment position during drag.
        Args:
            event: Mouse event.
        """
        if not self.is_dragging or not self.wire:
            return

        # 1. Get Current Position
        current_pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
        
        # If we didn't get a start pos in start(), grab it now (first move)
        if not self.drag_start_pos:
            self.drag_start_pos = current_pos
            return

        # 2. Calculate Delta
        dx = current_pos.x() - self.drag_start_pos.x()
        dy = current_pos.y() - self.drag_start_pos.y()

        # 3. Update Model Directly (Realtime)
        for idx, original_pos in self.initial_nodes.items():
            # Optional: Apply grid snapping logic here if desired
            new_x = original_pos[0] + dx
            new_y = original_pos[1] + dy
            
            # Simple snapping (can be delegated to API util)
            # new_x = round(new_x / 5.0) * 5.0
            # new_y = round(new_y / 5.0) * 5.0
            
            self.wire.path_nodes[idx] = [new_x, new_y]

        # 4. Sync scene item via API registry (never reference wire.ui_item)
        wire_item = self.api.get_scene_item(self.wire.id)
        if wire_item and hasattr(wire_item, '_rebuild_path'):
            wire_item._rebuild_path()
            wire_item.update()

    def on_mouse_release(self, event):
        """
        Handle mouse release event to finalize segment move and push command.
        Args:
            event: Mouse event.
        """
        if self.is_dragging and self.wire:
            # 1. Create Command
            # Get final positions from model
            final_start = self.wire.path_nodes[self.start_idx]
            final_end = self.wire.path_nodes[self.end_idx]
            
            if hasattr(self.api.context, 'undo_stack'):
                # Calculate dx, dy from initial to final positions
                dx = final_start[0] - self.initial_nodes[self.start_idx][0]
                dy = final_start[1] - self.initial_nodes[self.start_idx][1]
                cmd = MoveSegmentCommand(
                    self.wire,
                    self.start_idx,
                    self.end_idx,
                    dx,
                    dy,
                    self.api
                )
                cmd.mark_executed()
                self.api.context.undo_stack.push(cmd)

        # 2. Cleanup
        self.is_dragging = False
        self.wire = None
        self.initial_nodes = {}
        self.drag_start_pos = None
        
        if hasattr(self.api.tool_manager, 'set_tool'):
            self.api.tool_manager.set_tool('select')
            
        if hasattr(self.api, 'main_window') and self.api.main_window:
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)

    def cancel(self):
        """Revert changes."""
        if self.is_dragging and self.wire:
            for idx, original_pos in self.initial_nodes.items():
                self.wire.path_nodes[idx] = original_pos

            wire_item = self.api.get_scene_item(self.wire.id)
            if wire_item and hasattr(wire_item, '_rebuild_path'):
                wire_item._rebuild_path()
                wire_item.update()

        self.is_dragging = False
        self.wire = None
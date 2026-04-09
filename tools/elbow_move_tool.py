"""
Elbow move tool and command for wire elbow manipulation in Talus Trace.
Implements headless controller and undoable command for elbow movement.
"""

from tools.base_tool import BaseTool

class MoveElbowCommand:
    """
    Command to move a wire elbow to a new position, supporting undo/redo.
    """
    def __init__(self, wire, index, old_pos, new_pos, api=None):
        """
        Initialize the MoveElbowCommand.
        Args:
            wire: The wire object.
            index: Index of the elbow in path_nodes.
            old_pos: Previous position.
            new_pos: New position.
            api: APIManager instance for dispatch.
        """
        self.wire = wire
        self.index = index
        self.old_pos = old_pos
        self.new_pos = new_pos
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
        Move the wire elbow to the new position.
        """
        self.wire.path_nodes[self.index] = self.new_pos
        self._sync_scene()
        if self.api:
            self.api.dispatch("model_changed", {"action": "move_elbow", "item": self.wire})
        self.executed = True

    def undo(self):
        """
        Move the wire elbow back to the old position.
        """
        self.wire.path_nodes[self.index] = self.old_pos
        self._sync_scene()
        if self.api:
            self.api.dispatch("model_changed", {"action": "move_elbow", "item": self.wire})
        self.executed = False

    def redo(self):
        """
        Redo the elbow move operation.
        """
        self.execute()

    def mark_executed(self):
        """
        Mark the command as executed.
        """
        self.executed = True

class ElbowMoveTool(BaseTool):
    """
    Headless controller for wire elbow movement.
    """
    __guide__ = "ElbowMoveTool: Headless controller for wire elbow movement."

    def __init__(self):
        """
        Initialize the ElbowMoveTool.
        """
        super().__init__()
        self.wire = None
        self.index = None
        self.start_pos = None
        self.is_dragging = False

    def start(self, wire, index, *args, **kwargs):
        """
        Start the elbow move operation.
        Args:
            wire: The wire object.
            index: Index of the elbow in path_nodes.
        """
        self.wire = wire
        self.index = index
        if self.wire and 0 <= self.index < len(self.wire.path_nodes):
            self.start_pos = list(self.wire.path_nodes[self.index])
            self.is_dragging = True

    def on_mouse_press(self, event):
        """
        Handle mouse press event for elbow movement.
        Args:
            event: Mouse event.
        """
        pass

    def on_mouse_move(self, event):
        """
        Handle mouse move event for elbow movement.
        Args:
            event: Mouse event.
        """
        if not self.is_dragging or self.wire is None or self.index is None:
            return
        pos = getattr(event, 'scene_pos', None)
        if pos is None:
            return
        # Convert QPointF to [x, y] if needed
        if hasattr(pos, 'x') and hasattr(pos, 'y'):
            self.wire.path_nodes[self.index] = [float(pos.x()), float(pos.y())]
        else:
            self.wire.path_nodes[self.index] = list(pos)

    def on_mouse_release(self, event):
        """
        Handle mouse release event for elbow movement.
        Args:
            event: Mouse event.
        """
        if not self.is_dragging or self.wire is None or self.index is None:
            return
        pos = getattr(event, 'scene_pos', None)
        if pos is not None and hasattr(pos, 'x') and hasattr(pos, 'y'):
            new_pos = [float(pos.x()), float(pos.y())]
        else:
            new_pos = self.wire.path_nodes[self.index]
        cmd = MoveElbowCommand(self.wire, self.index, self.start_pos, new_pos)
        self.api.context.undo_stack.push(cmd)
        self.is_dragging = False
        self.wire = None
        self.index = None
        self.start_pos = None
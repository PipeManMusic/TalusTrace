
from tools.base_tool import BaseTool

class MoveElbowCommand:
    def __init__(self, wire, index, old_pos, new_pos):
        self.wire = wire
        self.index = index
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.executed = False

    def execute(self):
        self.wire.path_nodes[self.index] = self.new_pos
        self.executed = True

    def undo(self):
        self.wire.path_nodes[self.index] = self.old_pos
        self.executed = False

    def redo(self):
        self.execute()

    def mark_executed(self):
        self.executed = True

class ElbowMoveTool(BaseTool):
    __guide__ = "ElbowMoveTool: Headless controller for wire elbow movement."

    def __init__(self):
        super().__init__()
        self.wire = None
        self.index = None
        self.start_pos = None
        self.is_dragging = False

    def start(self, wire, index, *args, **kwargs):
        self.wire = wire
        self.index = index
        if self.wire and 0 <= self.index < len(self.wire.path_nodes):
            self.start_pos = list(self.wire.path_nodes[self.index])
            self.is_dragging = True

    def on_mouse_press(self, event):
        pass

    def on_mouse_move(self, event):
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
from infra.undo_stack import BaseCommand
from PySide6.QtCore import QPointF

class MoveSegmentCommand(BaseCommand):
    def __init__(self, wire, start_idx, end_idx, old_start, old_end, new_start, new_end):
        super().__init__("MoveSegmentCommand")
        self.wire = wire
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.old_start = old_start[:]
        self.old_end = old_end[:]
        self.new_start = new_start[:]
        self.new_end = new_end[:]
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def execute(self):
        self.api.move_segment(self.wire, self.start_idx, self.end_idx, self.new_start[0] - self.old_start[0], self.new_start[1] - self.old_start[1])

    def undo(self):
        self.api.move_segment(self.wire, self.start_idx, self.end_idx, self.old_start[0] - self.new_start[0], self.old_start[1] - self.new_start[1])


class SegmentMoveTool:
    __guide__ = "SegmentMoveTool: Handles wire segment movement and elbow creation."
    def on_mouse_press(self, scene_pos):
        # Alias to on_mouse_move for immediate drag start
        self.on_mouse_move(scene_pos)

    def deactivate(self):
        pass

    def __init__(self):
        self._wire_item = None
        self._start_idx = None
        self._end_idx = None
        self._original_start = None
        self._original_end = None
        self._ghost_start = None
        self._ghost_end = None

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self, wire_item, start_idx, end_idx, event=None):
        self._wire_item = wire_item
        self._start_idx = start_idx
        self._end_idx = end_idx
        self._original_start = wire_item.path_nodes[start_idx][:]
        self._original_end = wire_item.path_nodes[end_idx][:]
        self._ghost_start = self._original_start[:]
        self._ghost_end = self._original_end[:]
        # Save current selection
        from core.selection import SelectionManager
        self._prev_selection = SelectionManager().selected_models[:]
        if event is not None:
            self.on_mouse_press(event)

    def on_mouse_move(self, scene_pos):
        if self._wire_item and self._start_idx is not None and self._end_idx is not None:
            # scene_pos is a CanvasEvent, use its .scene_pos attribute (QPointF)
            x = scene_pos.scene_pos.x()
            y = scene_pos.scene_pos.y()
            # Compute delta from the midpoint of the original segment (no snapping for grip)
            orig_mid_x = (self._original_start[0] + self._original_end[0]) / 2
            orig_mid_y = (self._original_start[1] + self._original_end[1]) / 2
            dx = x - orig_mid_x
            dy = y - orig_mid_y
            # Snap elbows to grid, but not the grip
            from api.manager import APIManager
            api = APIManager.get_instance()
            new_start_x, new_start_y = api.snap_to_grid(self._original_start[0] + dx, self._original_start[1] + dy)
            new_end_x, new_end_y = api.snap_to_grid(self._original_end[0] + dx, self._original_end[1] + dy)
            new_start = [new_start_x, new_start_y]
            new_end = [new_end_x, new_end_y]
            self._ghost_start = new_start[:]
            self._ghost_end = new_end[:]
            self._wire_item.model.path_nodes[self._start_idx] = new_start
            self._wire_item.model.path_nodes[self._end_idx] = new_end
            # Robustly check if WireItem is deleted before calling methods
            try:
                if self._wire_item is not None:
                    # Only check for PySide6's wasDeleted if available
                    deleted = hasattr(self._wire_item, 'wasDeleted') and self._wire_item.wasDeleted() if hasattr(self._wire_item, 'wasDeleted') else False
                    if not deleted:
                        self._wire_item._build_path_and_grips()
            except RuntimeError:
                pass
            self._wire_item.update()

    def on_mouse_release(self, scene_pos):
        if self._wire_item is None:
            return
        # Use the actual grip position (no snapping), but elbows snap
        x = scene_pos.scene_pos.x()
        y = scene_pos.scene_pos.y()
        orig_mid_x = (self._original_start[0] + self._original_end[0]) / 2
        orig_mid_y = (self._original_start[1] + self._original_end[1]) / 2
        dx = x - orig_mid_x
        dy = y - orig_mid_y
        from api.manager import APIManager
        api = APIManager.get_instance()
        new_start_x, new_start_y = api.snap_to_grid(self._original_start[0] + dx, self._original_start[1] + dy)
        new_end_x, new_end_y = api.snap_to_grid(self._original_end[0] + dx, self._original_end[1] + dy)
        new_start = [new_start_x, new_start_y]
        new_end = [new_end_x, new_end_y]
        cmd = MoveSegmentCommand(self._wire_item.model, self._start_idx, self._end_idx, self._original_start, self._original_end, new_start, new_end)
        self._wire_item.model.ui_item = self._wire_item
        api.context.undo_stack.push(cmd)
        # Restore previous selection after move
        from core.selection import SelectionManager
        prev = getattr(self, '_prev_selection', None)
        if prev is not None:
            SelectionManager().set_selection(prev)
        self._wire_item = None
        self._start_idx = None
        self._end_idx = None
        self._original_start = None
        self._original_end = None
        self._ghost_start = None
        self._ghost_end = None
        api.tool_manager.set_tool('select')

    def cancel(self):
        self._wire_item = None
        self._start_idx = None
        self._end_idx = None
        self._original_start = None
        self._original_end = None
        self._ghost_start = None
        self._ghost_end = None

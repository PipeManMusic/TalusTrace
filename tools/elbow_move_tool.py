from infra.undo_stack import BaseCommand
from PySide6.QtCore import QPointF



class MoveElbowCommand(BaseCommand):
    def __init__(self, wire, index, old_pos, new_pos):
        super().__init__("MoveElbowCommand")
        self.wire = wire
        self.index = index
        self.old_pos = old_pos
        self.new_pos = new_pos
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def execute(self):
        self.api.move_elbow(self.wire, self.index, self.new_pos)

    def undo(self):
        self.api.move_elbow(self.wire, self.index, self.old_pos)


class ElbowMoveTool:
    def on_mouse_press(self, scene_pos):
        # Alias to on_mouse_move for immediate drag start
        self.on_mouse_move(scene_pos)

    def cancel(self):
        # ...removed debug print...
        self._wire_item = None
        self._elbow_index = None
        self._original_pos = None
        self._ghost_pos = None

    def __init__(self):
        self._wire_item = None
        self._elbow_index = None
        self._original_pos = None
        self._ghost_pos = None

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self, wire_item, elbow_index, event=None):
        # ...removed debug print...
        self._wire_item = wire_item
        self._elbow_index = elbow_index
        if wire_item is not None and elbow_index is not None:
            # ...removed debug print...
            pass
        else:
            # ...removed debug print...
            pass
        self._original_pos = wire_item.path_nodes[elbow_index][:] if wire_item is not None else None
        self._ghost_pos = self._original_pos[:] if self._original_pos is not None else None
        # Save current selection
        from core.selection import SelectionManager
        self._prev_selection = SelectionManager().selected_models[:]
        if event is not None:
            # ...removed debug print...
            self.on_mouse_press(event)

    def on_mouse_move(self, scene_pos):
        # ...removed debug print...
        if self._wire_item is None or self._elbow_index is None:
            # ...removed debug print...
            return
        # Only update the UI, do not touch the model or API during drag
        try:
            grips = self._wire_item.elbow_grips
        except RuntimeError:
            # ...removed debug print...
            self._wire_item = None
            return
        from api.manager import APIManager
        api = APIManager.get_instance()
        # scene_pos is a CanvasEvent, use its .scene_pos attribute (QPointF)
        x, y = api.snap_to_grid(scene_pos.scene_pos.x(), scene_pos.scene_pos.y())
        self._ghost_pos = [x, y]
        if grips and len(grips) > self._elbow_index - 1:
            grip = grips[self._elbow_index - 1]
            # ...removed debug print...
            try:
                grip.setPos(x, y)
            except RuntimeError:
                # ...removed debug print...
                pass
        # Redraw the wire visually (do not update model)
        try:
            # Make a temporary copy of path_nodes for visual feedback
            temp_nodes = list(self._wire_item.model.path_nodes)
            temp_nodes[self._elbow_index] = [x, y]
            self._wire_item._preview_path_nodes = temp_nodes
            self._wire_item._build_path_and_grips(path_nodes_override=temp_nodes)
            self._wire_item.update()
        except RuntimeError:
            # ...removed debug print...
            self._wire_item = None
            pass

    def on_mouse_release(self, scene_pos):
        # ...removed debug print...
        if self._wire_item is None:
            # ...removed debug print...
            return
        from api.manager import APIManager
        api = APIManager.get_instance()
        # scene_pos is a CanvasEvent, use its .scene_pos attribute (QPointF)
        x, y = api.snap_to_grid(scene_pos.scene_pos.x(), scene_pos.scene_pos.y())
        new_pos = [x, y]
        # ...removed debug print...
        # Commit the change to the model and API only now
        cmd = MoveElbowCommand(self._wire_item.model, self._elbow_index, self._original_pos, new_pos)
        self._wire_item.model.ui_item = self._wire_item
        api.context.undo_stack.push(cmd)
        # After command commit, reacquire new WireItem from model
        prev = getattr(self, '_prev_selection', None)
        if prev is not None:
            # Use APIManager to restore selection so UI is properly notified
            from api.manager import APIManager
            api = APIManager.get_instance()
            ids = [getattr(m, 'id', None) for m in prev if hasattr(m, 'id')]
            if ids:
                api.select(ids)
        # Clean up preview state
        if hasattr(self._wire_item, '_preview_path_nodes'):
            del self._wire_item._preview_path_nodes
        self._wire_item = None
        self._elbow_index = None
        self._original_pos = None
        self._ghost_pos = None
        api.tool_manager.set_tool('select')

    def deactivate(self):
        pass

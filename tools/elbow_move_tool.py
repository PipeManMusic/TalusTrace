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
        self.wire.path_nodes[self.index] = self.new_pos
        # Rebuild wire visuals if WireItem exists
        if hasattr(self.wire, 'ui_item') and self.wire.ui_item:
            self.wire.ui_item._build_path_and_grips()
            self.wire.ui_item.update()
        self.api.dispatch("model_changed", {"action": "move_elbow", "item": self.wire, "index": self.index})

    def undo(self):
        self.wire.path_nodes[self.index] = self.old_pos
        if hasattr(self.wire, 'ui_item') and self.wire.ui_item:
            self.wire.ui_item._build_path_and_grips()
            self.wire.ui_item.update()
        self.api.dispatch("model_changed", {"action": "move_elbow", "item": self.wire, "index": self.index})


class ElbowMoveTool:
    def on_mouse_press(self, scene_pos):
        # Alias to on_mouse_move for immediate drag start
        self.on_mouse_move(scene_pos)

    def cancel(self):
        print("[ElbowMoveTool] Cancelled move operation.")
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
        print(f"[ElbowMoveTool] start called: wire_item={wire_item}, elbow_index={elbow_index}, event={event}")
        self._wire_item = wire_item
        self._elbow_index = elbow_index
        if wire_item is not None and elbow_index is not None:
            print(f"[ElbowMoveTool] Initialized with wire_item id={id(wire_item)}, elbow_index={elbow_index}")
        else:
            print(f"[ElbowMoveTool] WARNING: start called with wire_item={wire_item}, elbow_index={elbow_index}")
        self._original_pos = wire_item.path_nodes[elbow_index][:] if wire_item is not None else None
        self._ghost_pos = self._original_pos[:] if self._original_pos is not None else None
        # Save current selection
        from core.selection import SelectionManager
        self._prev_selection = SelectionManager().selected_models[:]
        if event is not None:
            print(f"[ElbowMoveTool] start: forwarding event to on_mouse_press")
            self.on_mouse_press(event)

    def on_mouse_move(self, scene_pos):
        print(f"[ElbowMoveTool] on_mouse_move: scene_pos={scene_pos}")
        if self._wire_item is None or self._elbow_index is None:
            print("[ElbowMoveTool] WARNING: on_mouse_move called with no active wire item or elbow index.")
            return
        # Only update the UI, do not touch the model or API during drag
        try:
            grips = self._wire_item.elbow_grips
        except RuntimeError:
            print("[ElbowMoveTool] WARNING: WireItem has been deleted. Aborting move.")
            self._wire_item = None
            return
        from api.manager import APIManager
        api = APIManager.get_instance()
        # scene_pos is a CanvasEvent, use its .scene_pos attribute (QPointF)
        x, y = api.snap_to_grid(scene_pos.scene_pos.x(), scene_pos.scene_pos.y())
        self._ghost_pos = [x, y]
        if grips and len(grips) > self._elbow_index - 1:
            grip = grips[self._elbow_index - 1]
            print(f"[ElbowMoveTool] Moving grip visually to ({x}, {y})")
            try:
                grip.setPos(x, y)
            except RuntimeError:
                print("[ElbowMoveTool] WARNING: Grip has been deleted. Skipping visual move.")
        # Redraw the wire visually (do not update model)
        try:
            # Make a temporary copy of path_nodes for visual feedback
            temp_nodes = list(self._wire_item.model.path_nodes)
            temp_nodes[self._elbow_index] = [x, y]
            self._wire_item._preview_path_nodes = temp_nodes
            self._wire_item._build_path_and_grips(path_nodes_override=temp_nodes)
            self._wire_item.update()
        except RuntimeError:
            print("[ElbowMoveTool] WARNING: WireItem has been deleted during update. Aborting.")
            self._wire_item = None

    def on_mouse_release(self, scene_pos):
        print(f"[ElbowMoveTool] on_mouse_release: scene_pos={scene_pos}")
        if self._wire_item is None:
            print("[ElbowMoveTool] WARNING: on_mouse_release called with no active wire item.")
            return
        from api.manager import APIManager
        api = APIManager.get_instance()
        # scene_pos is a CanvasEvent, use its .scene_pos attribute (QPointF)
        x, y = api.snap_to_grid(scene_pos.scene_pos.x(), scene_pos.scene_pos.y())
        new_pos = [x, y]
        print(f"[ElbowMoveTool] Committing MoveElbowCommand from {self._original_pos} to {new_pos}")
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

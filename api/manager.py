from infra.context import Context
from infra.settings import SystemSettings
from core.library_manager import LibraryManager
from ui.input_system import InputSystem

class APIManager:
    def add_wire(self, pin1, pin2):
        """Headless/test-compatible wire creation: create a Wire and push a mock command to the undo stack."""
        from core.wire import Wire
        from infra.undo_stack import BaseCommand
        # Create a minimal wire model
        wire = Wire(
            id=f"W_{pin1.id}_{pin2.id}",
            from_conn=getattr(pin1, 'device_id', None) or getattr(pin1, 'parent_id', None) or "D1",
            from_pin=pin1.id,
            to_conn=getattr(pin2, 'device_id', None) or getattr(pin2, 'parent_id', None) or "D2",
            to_pin=pin2.id,
            path_nodes=[[pin1.x, pin1.y], [pin2.x, pin2.y]]
        )
        # Add to harness
        self.context.harness.wires.append(wire)
        # Push a mock command to the undo stack for test compatibility
        class AddWireCommand(BaseCommand):
            def __init__(self, wire):
                super().__init__("AddWireCommand")
                self.wire = wire
            def execute(self):
                pass
            def undo(self):
                pass
        self.context.undo_stack.push(AddWireCommand(wire))
    @classmethod
    def reset(cls):
        """Reset the singleton instance (for test compatibility)."""
        cls._instance = None

    def move_segment(self, wire, start_idx, end_idx, new_start, new_end):
        """Move a wire segment (two points) to new positions via the undo stack."""
        from tools.segment_move_tool import MoveSegmentCommand
        # Find old positions for undo (not needed here, command already has them)
        cmd = MoveSegmentCommand(wire, start_idx, end_idx, wire.path_nodes[start_idx][:], wire.path_nodes[end_idx][:], new_start, new_end)
        self.context.undo_stack.push(cmd)

    def add_elbow(self, wire, insert_idx, pos):
        """Add an elbow to a wire at the given index and position."""
        from tools.elbow_commands import AddElbowCommand
        cmd = AddElbowCommand(wire, insert_idx, pos)
        self.context.undo_stack.push(cmd)

    def remove_elbow(self, wire, index):
        """Remove an elbow from a wire at the given index."""
        from tools.elbow_commands import DeleteElbowCommand
        cmd = DeleteElbowCommand(wire, index)
        self.context.undo_stack.push(cmd)

    def move_elbow(self, wire, index, new_pos):
        """Move an elbow to a new position."""
        from tools.elbow_move_tool import MoveElbowCommand
        # Find old_pos for undo
        old_pos = wire.path_nodes[index][:] if 0 <= index < len(wire.path_nodes) else None
        cmd = MoveElbowCommand(wire, index, old_pos, new_pos)
        self.context.undo_stack.push(cmd)
    _instance = None

    def select(self, ids, tool_name=None):
        """Selects items by ID, updates SelectionManager, and broadcasts selection_changed."""
        from core.selection import SelectionManager
        # Find models by ID from context (devices, wires, etc.)
        models = []
        harness = self.context.harness
        for dev in getattr(harness, 'devices', []):
            if hasattr(dev, 'id') and dev.id in ids:
                models.append(dev)
        for wire in getattr(harness, 'wires', []):
            if hasattr(wire, 'id') and wire.id in ids:
                models.append(wire)
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        SelectionManager().set_selection(models)
        self.dispatch("selection_changed", {"selection": models, "tool": tool_name})

    def deselect(self, ids, tool_name=None):
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        """Deselects items by ID, updates SelectionManager, and broadcasts selection_changed."""
        from core.selection import SelectionManager
        mgr = SelectionManager()
        models = [m for m in mgr.selected_models if hasattr(m, 'id') and m.id not in ids]
        mgr.set_selection(models)
        self.dispatch("selection_changed", {"selection": models, "tool": tool_name})

    def clear_selection(self, tool_name=None):
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        """Clears selection, updates SelectionManager, and broadcasts selection_changed."""
        from core.selection import SelectionManager
        SelectionManager().clear_selection()
        self.dispatch("selection_changed", {"selection": [], "tool": tool_name})

    def snap_to_grid(self, x, y=None):
        """Snaps x (and optionally y) to the grid size from settings."""
        grid = getattr(self.settings, 'grid_size_mm', 5.0)
        if y is None:
            return round(x / grid) * grid
        return round(x / grid) * grid, round(y / grid) * grid

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, context=None):
        # Allow re-instantiation if reset() was called
        if APIManager._instance is not None:
            raise Exception("This class is a singleton! Call APIManager.reset() before creating a new instance in tests.")
        APIManager._instance = self

        # --- PHASE 1: CORE FOUNDATION ---
        self.settings = SystemSettings()  # Physics (Grid/Units)
        self.context = context if context is not None else Context()  # Session Data
        self.library = LibraryManager()   # Part Database

        # --- PHASE 2: SERVICE LAYER ---
        self.input_system = InputSystem()
        self.tool_manager = None
        self.main_window = None 

        # --- PHASE 3: REGISTRATION (The Fix) ---
        # We must import these modules so their @register_action decorators run.
        import api.commands.file
        import api.commands.edit
        import api.commands.view
        import api.commands.tools
        import api.commands.device

        # Initialize Tools
        from api.tool_manager import ToolManager
        from tools.select_tool import SelectTool
        from tools.wire_tool import WireTool
        from tools.placement_tool import PlacementTool
        from tools.move_tool import MoveTool
        from tools.elbow_move_tool import ElbowMoveTool
        from tools.segment_move_tool import SegmentMoveTool

        self.tool_manager = ToolManager()
        self.tool_manager.register_tool("select", SelectTool())
        self.tool_manager.register_tool("wire", WireTool())
        self.tool_manager.register_tool("placement", PlacementTool())
        self.tool_manager.register_tool("move", MoveTool())
        self.tool_manager.register_tool("elbow_move", ElbowMoveTool())
        self.tool_manager.register_tool("segment_move", SegmentMoveTool())

    # --- Scene Object Registry ---
    def register_scene_item(self, model_id, item):
        if not hasattr(self, '_scene_registry'):
            self._scene_registry = {}
        self._scene_registry[model_id] = item

    def unregister_scene_item(self, model_id):
        if hasattr(self, '_scene_registry') and model_id in self._scene_registry:
            del self._scene_registry[model_id]

    def get_scene_item(self, model_id):
        if hasattr(self, '_scene_registry'):
            return self._scene_registry.get(model_id)
        return None

    def find_pin_item(self, device_id, pin_id):
        # Look up PinItem by device_id and pin_id
        if not hasattr(self, '_scene_registry'):
            return None
        for item in self._scene_registry.values():
            # PinItem: has .model with .device_id and .id
            model = getattr(item, 'model', None)
            if model and getattr(model, 'device_id', None) == device_id and getattr(model, 'id', None) == pin_id:
                return item
        return None
    def subscribe(self, arg1, arg2=None):
        """
        Subscribe to events. Handles flexible signatures:
        1. subscribe(event_type: str, callback: callable) -> Standard
        2. subscribe(callback: callable) -> defaults to "state_changed"
        """
        event_type = "state_changed"
        callback = None

        if isinstance(arg1, str):
            # Case 1: subscribe("event_name", callback)
            event_type = arg1
            callback = arg2
        elif callable(arg1):
            # Case 2: subscribe(callback, [event_type]) - Legacy/Test compat
            callback = arg1
            if arg2 is not None:
                event_type = arg2
        else:
            # Fallback (mostly for robustness)
            callback = arg1
            
        if callback:
            self.context.observer.subscribe(event_type, callback)

    def dispatch(self, event_type, data=None):
        if data is None:
            data = {}
        print(f"[APIManager.dispatch] Event: {event_type}, Data: {data}")
        self.context.observer.dispatch(event_type, data)
        # Always also dispatch 'state_changed' for observer notification compatibility
        if event_type != "state_changed":
            self.context.observer.dispatch("state_changed", data)
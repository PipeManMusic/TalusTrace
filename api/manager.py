from infra.context import Context
from infra.settings import SystemSettings
from core.library_manager import LibraryManager
from ui.input_system import InputSystem

class APIManager:
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
        print(f"[APIManager.select] ids={ids} -> models={[type(m).__name__ + ':' + str(getattr(m, 'id', None)) for m in models]}")
        SelectionManager().set_selection(models)
        self.dispatch("selection_changed", {"selection": models, "tool": tool_name})

    def deselect(self, ids, tool_name=None):
        """Deselects items by ID, updates SelectionManager, and broadcasts selection_changed."""
        from core.selection import SelectionManager
        mgr = SelectionManager()
        models = [m for m in mgr.selected_models if hasattr(m, 'id') and m.id not in ids]
        mgr.set_selection(models)
        self.dispatch("selection_changed", {"selection": models, "tool": tool_name})

    def clear_selection(self, tool_name=None):
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

    def __init__(self):
        if APIManager._instance is not None:
            raise Exception("This class is a singleton!")

        # --- PHASE 1: CORE FOUNDATION ---
        self.settings = SystemSettings()  # Physics (Grid/Units)
        self.context = Context()          # Session Data
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

    def subscribe(self, event_type, callback):
        self.context.observer.subscribe(event_type, callback)

    def dispatch(self, event_type, data=None):
        if data is None: data = {}
        self.context.observer.dispatch(event_type, data)
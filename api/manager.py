"""
API Manager for Talus Trace.

This module defines the APIManager class, which acts as the main interface between the UI, core models, and infrastructure layers. It provides methods for manipulating devices, wires, selection, and scene items, and coordinates undo/redo, event dispatch, and tool management.
"""

Context = None
from infra.settings import SystemSettings
from core.library_manager import LibraryManager
from ui.input_system import InputSystem

class APIManager:
    """
    Main API manager for Talus Trace.

    This singleton class provides high-level methods for manipulating the project state, devices, wires, and UI integration. It manages the tool system, event dispatch, undo/redo, and scene item registry.
    """
    def handle_drop(self, event):
        """Handle drop events for the canvas, supporting library:// device insertion."""
        # Only handle QDropEvent with text starting with library://
        mime = event.mimeData() if hasattr(event, 'mimeData') else None
        if not mime or not mime.hasText():
            return
        text = mime.text()
        if not text.startswith("library://"):
            return
        part_id = text[len("library://"):]
        # Get part definition from library
        part_def = None
        if hasattr(self, 'library') and self.library:
            parts = self.library.get_parts()
            part_def = parts.get(part_id)
        if not part_def:
            return
        # Create device model and add to harness
        Device = self._get_device_model_class()
        # Get drop position in scene coordinates
        pos = event.position() if hasattr(event, 'position') else event.pos() if hasattr(event, 'pos') else None
        x, y = 0.0, 0.0
        if pos is not None:
            try:
                x, y = float(pos.x()), float(pos.y())
            except Exception:
                pass
        device = Device(
            id=part_id,
            library_id=part_id,
            x=x,
            y=y,
            pins=[{'id': p['id'], 'device_id': part_id, 'x': x, 'y': y} for p in part_def.get('pins', [])],
            meta=part_def
        )
        # Route device addition via infra command, not direct mutation
        from api.commands.device import AddDeviceCommand
        cmd = AddDeviceCommand(device)
        if hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(cmd)
        else:
            cmd.execute()
        # Optionally, trigger scene update if needed
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.load_harness(self.context.harness)

    def _get_device_model_class(self):
        """
        Helper to get the Device model class.
        Returns the Device class from core.device, or a minimal fallback if import fails.
        """
        try:
            from core.device import Device
            return Device
        except ImportError:
            # Fallback: create a minimal Device class
            return lambda **kwargs: type('Device', (), kwargs)()
        
    def move_device(self, target_or_id, new_x, new_y, commit=False):
        """
        Move a device or scene item. If commit=True, push MoveCommand to undo stack; else, update model and dispatch only.
        If commit is False, update model and dispatch for real-time feedback (drag).
        If commit is True, push MoveCommand for undo/redo (on drag finish).
        """
        from api.commands.move import MoveCommand
        device = None
        # Always resolve device and scene item from id if possible
        if hasattr(target_or_id, 'model'):
            scene_item = target_or_id
            device = getattr(scene_item, 'model', None)
        else:
            device_id = target_or_id
            for dev in getattr(self.context.harness, 'devices', []):
                if hasattr(dev, 'id') and dev.id == device_id:
                    device = dev
                    break
            # Try to get scene item from registry
            scene_item = self.get_scene_item(device_id)
        if device is None:
            return
        if commit:
            # Use the original drag start position for undo, if available
            old_x, old_y = None, None
            if hasattr(scene_item, '_drag_initial_pos'):
                old_x, old_y = scene_item._drag_initial_pos
            else:
                old_x, old_y = getattr(device, 'x', 0.0), getattr(device, 'y', 0.0)
            target = scene_item if scene_item is not None else device
            if scene_item is None and hasattr(device, 'mock_item'):
                target = getattr(device, 'mock_item')
            cmd = MoveCommand(target, (old_x, old_y), (new_x, new_y))
            if hasattr(self.context, 'undo_stack'):
                self.context.undo_stack.push(cmd)
            else:
                cmd.execute()
        else:
            # Directly update model for real-time feedback
            device.x = new_x
            device.y = new_y
            self.dispatch("model_changed", {"action": "move", "item": device})
    def open_context_menu(self, event):
        """
        Open a context menu at the event location, dispatching a 'context_menu' event.
        Handles both device and canvas context menus, and supports headless/test mode.
        """
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        from PySide6.QtCore import QPoint
        view = getattr(self, 'main_window', None)
        if not view:
            event.accept()
            return
        canvas = getattr(view, 'canvas', None)
        if not canvas:
            event.accept()
            return
        # Robust hit test: use event's global position to map to viewport, then to scene
        mapped_scene_pos = None
        item = None
        if hasattr(event, 'globalPos') and hasattr(canvas, 'mapFromGlobal'):
            viewport_pos = canvas.mapFromGlobal(event.globalPos())
            mapped_scene_pos = canvas.mapToScene(viewport_pos)
            item = canvas.scene.itemAt(mapped_scene_pos, canvas.transform())
        else:
            scene_pos = event.pos() if hasattr(event, 'pos') else None
            if scene_pos is not None:
                mapped_scene_pos = canvas.mapToScene(scene_pos)
                item = canvas.scene.itemAt(mapped_scene_pos, canvas.transform())
        menu = QMenu(view)
        # Default actions
        if item and hasattr(item, 'model'):
            action = QAction('Device Action', menu)
            menu.addAction(action)
        else:
            action = QAction('Canvas Action', menu)
            menu.addAction(action)
        # Always provide scene_pos for event dispatch
        dispatch_scene_pos = mapped_scene_pos if mapped_scene_pos is not None else None
        self.dispatch('context_menu', {'menu': menu, 'item': item, 'scene_pos': dispatch_scene_pos, 'event': event})
        global_pos = event.globalPos() if hasattr(event, 'globalPos') else None
        import os
        is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
        if global_pos and not is_headless:
            menu.exec(global_pos)
        elif hasattr(self, '_test_context_menu_hook'):
            self._test_context_menu_hook(menu, global_pos)
        event.accept()

    def deselect_all(self):
        """Clears all selection for SelectTool compatibility."""
        self.clear_selection()
    def add_wire(self, wire):
        """
        Accept a fully-formed Wire object (with valid UUID id) and push a real AddWireCommand to the undo stack.
        The API must not generate or mutate IDs; this is handled by the infra/model layer.
        """
        from api.commands.device import AddWireCommand
        self.context.undo_stack.push(AddWireCommand(wire))
    @classmethod
    def reset(cls):
        """Reset the singleton instance (for test compatibility)."""
        cls._instance = None

    def move_segment(self, wire, start_idx, end_idx, dx, dy):
        """Move a wire segment by delta values (dx, dy) via the undo stack."""
        from tools.segment_move_tool import MoveSegmentCommand
        # Pass delta values to the command
        cmd = MoveSegmentCommand(wire, start_idx, end_idx, dx, dy, self)
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
        """
        Deselects items by ID, updates SelectionManager, and broadcasts selection_changed.
        """
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
        """
        Clears selection, updates SelectionManager, and broadcasts selection_changed.
        """
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
    def get_instance(cls, context=None):
        """
        Get the singleton instance of APIManager, optionally injecting a new context.
        """
        if cls._instance is None:
            cls._instance = cls(context=context)
        elif context is not None:
            # If a context is provided and instance exists, update its context (for test injection)
            cls._instance.context = context
        return cls._instance

    def __init__(self, context=None):
        """
        Initialize the APIManager singleton, setting up settings, context, library, tools, and service layer.
        Raises an exception if an instance already exists (unless reset() was called).
        """
        global Context
        if Context is None:
            from infra.context import Context
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
        """
        Register a scene item (UI object) with a model ID for lookup and selection.
        """
        if not hasattr(self, '_scene_registry'):
            self._scene_registry = {}
        self._scene_registry[model_id] = item

    def unregister_scene_item(self, model_id):
        """
        Unregister a scene item by its model ID.
        """
        if hasattr(self, '_scene_registry') and model_id in self._scene_registry:
            del self._scene_registry[model_id]

    def get_scene_item(self, model_id):
        """
        Retrieve a registered scene item by its model ID.
        Returns None if not found.
        """
        if hasattr(self, '_scene_registry'):
            return self._scene_registry.get(model_id)
        return None

    def find_pin_item(self, device_id, pin_id):
        """
        Look up a PinItem by device_id and pin_id in the scene registry.
        Returns the item if found, else None.
        """
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
        """
        Dispatch an event to all observers, and always dispatch 'state_changed' for compatibility.
        """
        if data is None:
            data = {}
        self.context.observer.dispatch(event_type, data)
        # Always also dispatch 'state_changed' for observer notification compatibility
        if event_type != "state_changed":
            self.context.observer.dispatch("state_changed", data)
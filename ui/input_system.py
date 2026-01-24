"""
Input system for Talus Trace UI.

Handles keyboard shortcuts, tool dispatch, and event routing for the canvas.
"""

import yaml
import os
from PySide6.QtCore import QObject, QEvent, Qt
from api.actions import registry

class InputSystem(QObject):
    """Manages keyboard shortcuts, tool dispatch, and event routing for the canvas."""
    import api.edit_delete_action  # Ensure edit.delete action is registered
    def __init__(self, config_path=None, move_tool=None):
        """Initialize InputSystem with optional config path and move tool for testing."""
        super().__init__()
        self.canvas = None
        self.config_path = config_path
        self.global_keymap = {}  # {Qt.Key: action_id}
        self._move_tool = move_tool  # Allow dependency injection for tests

        # Register edit.delete action (avoids circular import)
        import api.edit_delete_action

        # 1. Load Defaults (Safety Net)
        self._load_defaults()

        # 2. Override with Config if available
        if self.config_path:
            self._load_keymap()

    def register_shortcut(self, key, action_id):
        """Register a shortcut mapping (key: Qt.Key or str, action_id: str)."""
        if isinstance(key, str):
            qt_key = getattr(Qt, f"Key_{key.upper()}", None)
            if qt_key is not None:
                self.global_keymap[qt_key] = action_id
        else:
            self.global_keymap[key] = action_id

    def _load_defaults(self):
        """Ensure critical shortcuts work out-of-the-box."""
        self.global_keymap[Qt.Key_Z] = "edit.undo"
        self.global_keymap[Qt.Key_Y] = "edit.redo"
        self.global_keymap[Qt.Key_Delete] = "edit.delete"
        self.global_keymap[Qt.Key_R] = "edit.rotate_cw"

    @property
    def api(self):
        """Return the singleton APIManager instance."""
        from api.manager import APIManager
        return APIManager.get_instance()

    def install(self, canvas):
        """Connect the InputSystem to the Canvas widget as an event filter."""
        self.canvas = canvas
        if self.canvas:
            self.canvas.installEventFilter(self)

    def handle_canvas_event(self, event):
        """Route mouse events from the Canvas to the active tool or injected MoveTool."""
        etype = event.original_event.type()
        # 1. Right Click Handling (Context Menu)
        if etype == QEvent.MouseButtonPress:
            is_right_click = hasattr(event, 'button') and event.button == Qt.RightButton
            if is_right_click:
                # If we have a hit item, select it first (optional UX choice)
                if event.scene_item and hasattr(self.api, 'select_device'):
                    # self.api.select_device(...) # logic to select under cursor
                    pass
                if hasattr(self.api, 'open_context_menu'):
                    self.api.open_context_menu(event.original_event)
                    return True

        # 2. Tool Handling
        tool = self._move_tool if self._move_tool is not None else self.api.tool_manager.active_tool
        from core.selection import SelectionManager
        selection_ids = SelectionManager().current_selection_ids
        is_move_tool = tool.__class__.__name__ == "MoveTool"
        scene_pos = getattr(event, 'scene_pos', None)
        item = getattr(event, 'scene_item', None)
        # Always call on_mouse_press/move/release if present for test compatibility
        if tool:
            if etype == QEvent.MouseButtonPress:
                if hasattr(tool, 'start_drag'):
                    if is_move_tool:
                        if selection_ids and item is not None and hasattr(item, 'model') and getattr(item.model, 'id', None) in selection_ids:
                            tool.start_drag(item, scene_pos)
                        elif item is not None and hasattr(item, 'model') and getattr(item.model, 'id', None) not in selection_ids:
                            self.api.select([item.model.id], tool_name="move")
                    else:
                        tool.start_drag(item, scene_pos)
                if hasattr(tool, 'on_mouse_press'):
                    tool.on_mouse_press(event)
            elif etype == QEvent.MouseMove:
                if hasattr(tool, 'update_drag'):
                    if is_move_tool:
                        if selection_ids:
                            tool.update_drag(scene_pos)
                    else:
                        tool.update_drag(scene_pos)
                if hasattr(tool, 'on_mouse_move'):
                    tool.on_mouse_move(event)
            elif etype == QEvent.MouseButtonRelease:
                if hasattr(tool, 'finish_drag'):
                    if is_move_tool:
                        if selection_ids:
                            tool.finish_drag(scene_pos)
                    else:
                        tool.finish_drag(scene_pos)
                if hasattr(tool, 'on_mouse_release'):
                    tool.on_mouse_release(event)
        return False

    def eventFilter(self, obj, event):
        """Capture global key presses (shortcuts) and handle them if mapped."""
        if event.type() == QEvent.KeyPress:
            if self._handle_key(event):
                return True
        return super().eventFilter(obj, event)

    def _handle_key(self, event):
        """Handle a key event, executing mapped actions or shortcuts if present."""
        key = event.key()
        modifiers = event.modifiers()
        print(f"[DEBUG] _handle_key called: key={key}, modifiers={modifiers}")

        # 1. Check Global Keymap
        # Handle Modifier Logic (Simple implementation for Ctrl+Z)
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Z:
                print("[DEBUG] Ctrl+Z detected, executing edit.undo")
                registry.execute("edit.undo", self.api.context)
                return True
            if key == Qt.Key_Y:
                print("[DEBUG] Ctrl+Y detected, executing edit.redo")
                registry.execute("edit.redo", self.api.context)
                return True

        # 2. Simple Keymap Lookup (Single keys like 'R' or 'Delete')
        if key in self.global_keymap:
            action_id = self.global_keymap[key]
            print(f"[DEBUG] Key {key} mapped to action {action_id}")
            # Avoid re-triggering undo/redo if caught above
            if action_id in ["edit.undo", "edit.redo"] and not (modifiers & Qt.ControlModifier):
                 print("[DEBUG] Ignoring z/y without ctrl")
                 pass # Ignore 'z' without ctrl
            else:
                print(f"[DEBUG] Executing action {action_id} via registry")
                registry.execute(action_id, self.api.context)
                return True

        print(f"[DEBUG] No action mapped for key {key}")
        return False

    def _load_keymap(self):
        """Parse the YAML config for keymap definitions, supporting 'global' and 'commands' sections."""
        if not self.config_path or not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                # Support legacy 'commands' section
                commands = data.get('commands', [])
                for cmd in commands:
                    key_char = cmd.get('default_key')
                    action_id = cmd.get('id')
                    if key_char and action_id:
                        key_name = f"Key_{key_char.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            self.global_keymap[qt_key] = action_id
                # Support new 'global' section
                global_map = data.get('global', {})
                for key_str, action_id in global_map.items():
                    # Handle modifier keys (e.g., Ctrl+Z)
                    if key_str.startswith("Ctrl+"):
                        base_key = key_str.split("+")[1]
                        key_name = f"Key_{base_key.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            # Store tuple (key, modifier) for lookup
                            self.global_keymap[(qt_key, Qt.ControlModifier)] = action_id
                    else:
                        key_name = f"Key_{key_str.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            self.global_keymap[qt_key] = action_id
        except Exception as e:
            pass
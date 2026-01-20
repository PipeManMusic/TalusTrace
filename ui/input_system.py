import yaml
import os
from PySide6.QtCore import QObject, QEvent, Qt

class InputSystem(QObject):
    def __init__(self, config_path=None, move_tool=None):
        super().__init__()
        self.canvas = None
        self.config_path = config_path
        self.global_keymap = {}  # {Qt.Key: action_id}
        self._move_tool = move_tool  # Allow injection for testing

        if self.config_path:
            self._load_keymap()

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    @property
    def key_map(self):
        """Exposes the internal keymap for testing/debugging."""
        return self.global_keymap

    def install(self, canvas):
        """Connects the InputSystem to the Canvas widget."""
        self.canvas = canvas
        if self.canvas:
            self.canvas.installEventFilter(self)

    def handle_canvas_event(self, event):
        """Routes mouse events from the Canvas to the Active Tool, or MoveTool for device drag."""
        tool = self.api.tool_manager.active_tool
        etype = event.original_event.type()

        # 1. Auto-deselect if left-clicking empty space (not right-click)
        if etype == QEvent.MouseButtonPress:
            is_right_click = hasattr(event, 'button') and event.button == Qt.RightButton
            if not event.scene_item and not is_right_click:
                self.api.clear_selection(tool_name="InputSystem")

        # 1b. Show context menu if right-clicking on a device
        if etype == QEvent.MouseButtonPress:
            is_right_click = hasattr(event, 'button') and event.button == Qt.RightButton
            is_device = hasattr(event.scene_item, 'model')
            print(f'[InputSystem] MouseButtonPress: is_right_click={is_right_click}, is_device={is_device}')
            if is_right_click and is_device:
                print('[InputSystem] Calling api.open_context_menu for device')
                self.api.open_context_menu(event.original_event)
                return True

        # --- Always route drag events on device items to MoveTool and block native propagation ---
        from tools.move_tool import MoveTool
        if not hasattr(self, '_move_tool') or self._move_tool is None:
            self._move_tool = MoveTool()
        self._move_tool.api = self.api
        move_tool = self._move_tool

        is_device = hasattr(event.scene_item, 'model')
        is_drag_event = etype in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease)

        # If a drag is in progress, always route to MoveTool until drag ends
        if getattr(move_tool, 'is_dragging', False):
            if etype == QEvent.MouseMove and hasattr(move_tool, 'on_mouse_move'):
                move_tool.on_mouse_move(event)
                return True
            elif etype == QEvent.MouseButtonRelease and hasattr(move_tool, 'on_mouse_release'):
                move_tool.on_mouse_release(event)
                return True

        # Start drag on device item
        if is_device and is_drag_event:
            if etype == QEvent.MouseButtonPress and hasattr(move_tool, 'on_mouse_press'):
                move_tool.on_mouse_press(event)
                return True
            # If drag is not in progress, do not handle move/release here

        # 2. Forward to tool
        if etype == QEvent.MouseButtonPress and hasattr(tool, 'on_mouse_press'):
            tool.on_mouse_press(event)
        elif etype == QEvent.MouseButtonRelease and hasattr(tool, 'on_mouse_release'):
            tool.on_mouse_release(event)
        elif etype == QEvent.MouseMove and hasattr(tool, 'on_mouse_move'):
            tool.on_mouse_move(event)
        return False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if self._handle_key(event):
                return True
        return super().eventFilter(obj, event)

    def _handle_key(self, event):
        key = event.key()

        # 1. Check Global Keymap (Actions)
        if key in self.global_keymap:
            action_id = self.global_keymap[key]
            from api.actions import registry
            # FIX: Use .execute() instead of subscripting
            if action_id in registry:
                registry.execute(action_id, self.api.context)
                return True

        # 2. Tool Logic
        tool = self.api.tool_manager.active_tool
        
        # 2a. Cancel (Escape)
        if key == Qt.Key_Escape:
            if tool and hasattr(tool, 'cancel'):
                tool.cancel()
                return True

        # 2b. Forward to Tool
        if tool and hasattr(tool, 'on_key_press'):
            tool.on_key_press(event)
            return True

        return False

    def register_shortcut(self, key, action_id):
        """Registers a runtime shortcut (used by tests)."""
        # Supports both Qt.Key (int) and string shortcuts
        self.global_keymap[key] = action_id

    def _load_keymap(self):
        """Parses the YAML config to build the global keymap."""
        # Only proceed if config_path is a valid path type
        if not self.config_path or not isinstance(self.config_path, (str, bytes, os.PathLike)):
            return
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                commands = data.get('commands', [])
                for cmd in commands:
                    key_char = cmd.get('default_key')
                    action_id = cmd.get('id')
                    if key_char and action_id:
                        key_name = f"Key_{key_char.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            self.global_keymap[qt_key] = action_id
        except Exception as e:
            print(f"Failed to load keymap: {e}")
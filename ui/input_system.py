import yaml
import os
from PySide6.QtCore import QObject, QEvent, Qt

class InputSystem(QObject):
    def __init__(self, config_path=None):
        super().__init__()
        self.canvas = None
        self.config_path = config_path
        self.global_keymap = {}  # {Qt.Key: action_id}

        if self.config_path:
            self._load_keymap()

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    @property
    def key_map(self):
        return self.global_keymap

    def install(self, canvas):
        self.canvas = canvas
        if self.canvas:
            self.canvas.installEventFilter(self)

    def register_shortcut(self, key, action_id):
        self.global_keymap[key] = action_id

    def _load_keymap(self):
        if not os.path.exists(self.config_path):
            print(f"DEBUG: Config file not found at {self.config_path}")
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
                            print(f"DEBUG: Mapped {key_name} ({qt_key}) to {action_id}")
                        else:
                            print(f"DEBUG: Qt has no key named {key_name}")
                    else:
                        print(f"DEBUG: Invalid command entry: {cmd}")
        except Exception as e:
            print(f"DEBUG: Failed to load keymap: {e}")

    def eventFilter(self, obj, event):
        
        # PySide6 Event Type Matching
        if event.type() == QEvent.KeyPress:
            if self._handle_key(event):
                return True
        return super().eventFilter(obj, event)

    def _handle_key(self, event):
        key = event.key()

        if key in self.global_keymap:
            action_id = self.global_keymap[key]
            from api.actions import registry
            
            
            if action_id in registry:
                registry.execute(action_id, self.api.context)
                return True
            else:

        # Tool Logic
        tool = self.api.tool_manager.active_tool
        if tool and hasattr(tool, 'on_key_press'):
            return tool.on_key_press(event)

        return False

    def handle_canvas_event(self, event):
        """Routes mouse events from the Canvas to the Active Tool."""
        tool = self.api.tool_manager.active_tool
        if not tool:
            return

        # Map QEvent type from the underlying view event
        etype = event.original_event.type()

        # 1. Auto-deselect if clicking empty space (Standard behavior)
        if etype == QEvent.MouseButtonPress:
            if not event.scene_item:
                 self.api.clear_selection(tool_name="InputSystem")

        # 2. Forward to tool based on event type
        if etype == QEvent.MouseButtonPress and hasattr(tool, 'on_mouse_press'):
            tool.on_mouse_press(event)
        elif etype == QEvent.MouseButtonRelease and hasattr(tool, 'on_mouse_release'):
            tool.on_mouse_release(event)
        elif etype == QEvent.MouseMove and hasattr(tool, 'on_mouse_move'):
            tool.on_mouse_move(event)
        elif etype == QEvent.MouseButtonDblClick and hasattr(tool, 'on_double_click'):
             # Optional: Handle double click if tool supports it
             tool.on_double_click(event)

        def eventFilter(self, obj, event):
            # DEBUG: Print event type
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
                if action_id in registry:
                    registry[action_id](self.api.context)
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

        def handle_canvas_event(self, event):
            """Routes mouse events from the Canvas to the Active Tool."""
            tool = self.api.tool_manager.active_tool
            if not tool:
                return

            etype = event.original_event.type()
        
            # Auto-deselect if clicking empty space
            if etype == QEvent.MouseButtonPress:
                if not event.scene_item:
                     self.api.clear_selection(tool_name="InputSystem")

            # Forward to tool
            if etype == QEvent.MouseButtonPress and hasattr(tool, 'on_mouse_press'):
                tool.on_mouse_press(event)
            elif etype == QEvent.MouseButtonRelease and hasattr(tool, 'on_mouse_release'):
                tool.on_mouse_release(event)
            elif etype == QEvent.MouseMove and hasattr(tool, 'on_mouse_move'):
                tool.on_mouse_move(event)

        @property
        def api(self):
            """Lazy load APIManager to avoid circular imports."""
            from api.manager import APIManager
            return APIManager.get_instance()

        def install(self, canvas):
            """Connects the InputSystem to the Canvas widget."""
            self.canvas = canvas
            if self.canvas:
                self.canvas.installEventFilter(self)

        def register_shortcut(self, key, action_id):
            """Registers a runtime shortcut (used by tests)."""
            self.global_keymap[key] = action_id

        def _load_keymap(self):
            """Parses the YAML config to build the global keymap."""
            try:
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)
                    commands = data.get('commands', [])
                    for cmd in commands:
                        key_char = cmd.get('default_key')
                        action_id = cmd.get('id')
                        if key_char and action_id:
                            # Robust lookup: 'G' -> Qt.Key_G
                            key_name = f"Key_{key_char.upper()}"
                            if hasattr(Qt, key_name):
                                qt_key = getattr(Qt, key_name)
                                self.global_keymap[qt_key] = action_id
            except Exception as e:
                print(f"Failed to load keymap: {e}")

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
                if action_id in registry:
                    registry[action_id](self.api.context)
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

        def handle_canvas_event(self, event):
            """Routes mouse events from the Canvas to the Active Tool."""
            tool = self.api.tool_manager.active_tool
            if not tool:
                return

            etype = event.original_event.type()
        
            # Auto-deselect if clicking empty space
            if etype == QEvent.MouseButtonPress:
                if not event.scene_item:
                     self.api.clear_selection(tool_name="InputSystem")

            # Forward to tool
            if etype == QEvent.MouseButtonPress and hasattr(tool, 'on_mouse_press'):
                tool.on_mouse_press(event)
            elif etype == QEvent.MouseButtonRelease and hasattr(tool, 'on_mouse_release'):
                tool.on_mouse_release(event)
            elif etype == QEvent.MouseMove and hasattr(tool, 'on_mouse_move'):
                tool.on_mouse_move(event)
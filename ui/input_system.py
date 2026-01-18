from PySide6.QtCore import QObject, QEvent, Qt

class InputSystem(QObject):
    def __init__(self):
        super().__init__()
        self.canvas = None
        # REMOVED: self._api = APIManager.get_instance() 
        # This was causing the infinite recursion loop.

    @property
    def api(self):
        """
        Lazy load APIManager. 
        This ensures we don't try to get the instance before it's fully initialized.
        """
        from api.manager import APIManager
        return APIManager.get_instance()

    def install(self, canvas):
        """
        Registers the canvas with the input system.
        - Mouse events are forwarded explicitly by the Canvas.
        - This method installs an event filter for Keyboard events.
        """
        self.canvas = canvas
        if self.canvas:
            self.canvas.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            return self._handle_key(event)
        return super().eventFilter(obj, event)

    def _handle_key(self, event):
        # Check for cancel key mapping from UI YAML (default: Escape)
        cancel_key = Qt.Key_Escape
        try:
            import yaml, os
            path = os.path.join("resources", "config", "ui_layout.yaml")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
                    keymap = config.get('keymap', {})
                    cancel_key = getattr(Qt, keymap.get('cancel', 'Key_Escape'), Qt.Key_Escape)
        except Exception as e:
            # ...removed debug print...
            pass

        if event.key() == cancel_key:
            tool = self.api.tool_manager.active_tool
            if tool and hasattr(tool, 'cancel'):
                # ...removed debug print...
                tool.cancel()
                return True

        tool = self.api.tool_manager.active_tool
        if tool and hasattr(tool, 'on_key_press'):
            tool.on_key_press(event)
            return True
        return False

    def handle_canvas_event(self, event):
        # Centralized blank canvas click handling
        tool = self.api.tool_manager.active_tool
        if not tool:
            return

        etype = event.original_event.type()

        # On mouse press, if no item is under cursor, always clear selection
        if etype == QEvent.MouseButtonPress:
            if not event.scene_item:
                # ...removed debug print...
                self.api.clear_selection(tool_name="InputSystem")
            if hasattr(tool, 'on_mouse_press'):
                tool.on_mouse_press(event)
        elif etype == QEvent.MouseButtonRelease:
            if hasattr(tool, 'on_mouse_release'):
                tool.on_mouse_release(event)
        elif etype == QEvent.MouseMove:
            if hasattr(tool, 'on_mouse_move'):
                tool.on_mouse_move(event)
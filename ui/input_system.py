import yaml
from pathlib import Path
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit
from api.actions import registry

class InputSystem(QObject):
    def __init__(self, config_path: str = "resources/config/actions.yaml"):
        super().__init__()
        self.key_map = {}
        self._shortcuts = self.key_map  # Alias for test compatibility
        self._load_config(config_path)

    def register_shortcut(self, key: str, action_id: str):
        """Register a shortcut key to an action id."""
        self._shortcuts[key] = action_id

    def process_key_sequence(self, key: str):
        """Simulate processing a key sequence (for testing)."""
        if key in self._shortcuts:
            action_id = self._shortcuts[key]
            registry.execute(action_id)
            return True
        return False

    def install(self):
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    def _load_config(self, path: str):
        if not Path(path).exists():
            return
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if not data: return
                for cmd in data.get("commands", []):
                    aid = cmd.get('id')
                    if "default_key" in cmd:
                        seq = QKeySequence(cmd["default_key"]).toString()
                        self.key_map[seq] = aid
        except Exception as e:
            print(f"Failed to load keymap: {e}")

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            # 1. Ignore text inputs
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                return False 

            # 2. Get Key Sequence (Qt6 Compliant)
            # keyCombination() returns the Key + Modifiers safely
            sequence = QKeySequence(event.keyCombination()).toString()
            
            if sequence in self.key_map:
                action_id = self.key_map[sequence]
                registry.execute(action_id)
                return True

        return super().eventFilter(obj, event)

    def handle_canvas_event(self, event):
        """
        Central event dispatcher for canvas events.
        Dispatches to the active tool based on the type of the original Qt event.
        """
        from api.manager import APIManager
        tool = APIManager.get_instance().tool_manager.active_tool
        if not tool or not hasattr(event, 'original_event'):
            return
        qt_event = event.original_event
        if qt_event and hasattr(qt_event, 'type'):
            etype = qt_event.type()
            from PySide6.QtCore import QEvent
            if etype == QEvent.MouseButtonPress:
                tool.on_mouse_press(event)
            elif etype == QEvent.MouseButtonRelease:
                tool.on_mouse_release(event)
            elif etype == QEvent.MouseMove:
                tool.on_mouse_move(event)
            elif etype == QEvent.MouseButtonDblClick:
                tool.on_mouse_double_click(event)
        # Optionally: handle wheel, context menu, etc.
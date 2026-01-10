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
        self._load_config(config_path)

    def install(self):
        app = QApplication.instance()
        if app: app.installEventFilter(self)

    def _load_config(self, path: str):
        if not Path(path).exists(): return
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if not data: return
                for cmd in data.get("commands", []):
                    if "default_key" in cmd:
                        self.register_shortcut(cmd["default_key"], cmd["id"])
        except Exception as e:
            print(f"Failed to load keymap: {e}")

    # RESTORED FEATURE
    def register_shortcut(self, key_seq, action_id):
        seq = QKeySequence(key_seq).toString()
        self.key_map[seq] = action_id

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            if isinstance(QApplication.focusWidget(), (QLineEdit, QTextEdit)):
                return False 
            seq = QKeySequence(event.keyCombination()).toString()
            if seq in self.key_map:
                registry.execute(self.key_map[seq])
                return True
        return super().eventFilter(obj, event)

    def handle_canvas_event(self, event):
        from api.manager import APIManager
        tool = APIManager.get_instance().tool_manager.active_tool
        if tool and hasattr(event, 'original_event'):
            etype = event.original_event.type()
            if etype == QEvent.MouseMove: tool.on_mouse_move(event)
            elif etype == QEvent.MouseButtonPress: tool.on_mouse_press(event)
            elif etype == QEvent.MouseButtonRelease: tool.on_mouse_release(event)
            elif etype == QEvent.MouseButtonDblClick: getattr(tool, 'on_mouse_double_click', lambda e: None)(event)

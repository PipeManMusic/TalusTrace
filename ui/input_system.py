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
        self._shortcuts = self.key_map
        self._load_config(config_path)

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
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                return False 
            sequence = QKeySequence(event.keyCombination()).toString()
            if sequence in self.key_map:
                registry.execute(self.key_map[sequence])
                return True
        return super().eventFilter(obj, event)

    def handle_canvas_event(self, event):
        """Central dispatcher that routes CanvasEvents to the active tool."""
        from api.manager import APIManager
        tool = APIManager.get_instance().tool_manager.active_tool
        if not tool or not hasattr(event, 'original_event'):
            return
        
        etype = event.original_event.type()
        if etype == QEvent.MouseMove:
            tool.on_mouse_move(event)
        elif etype == QEvent.MouseButtonPress:
            tool.on_mouse_press(event)
        elif etype == QEvent.MouseButtonRelease:
            tool.on_mouse_release(event)
        elif etype == QEvent.MouseButtonDblClick:
            tool.on_mouse_double_click(event)
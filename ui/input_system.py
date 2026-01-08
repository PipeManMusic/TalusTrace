import yaml
from typing import Dict
from pathlib import Path
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit
from api.actions import registry

class InputSystem(QObject):
    def handle_event(self, event):
        # Minimal logic for test
        # Only handle QKeyEvent with mapped key
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeySequence
        if event.type() == QEvent.KeyPress:
            seq = QKeySequence(event.key()).toString()
            if seq in self.key_map:
                from api.actions import registry
                registry.execute(self.key_map[seq])
                return True
        return False

    """
    Global Input Interceptor.
    Installs itself as an EventFilter on the QApplication to catch
    shortcuts regardless of which widget has focus.
    """
    def __init__(self, config_path: str = "resources/config/actions.yaml"):
        super().__init__()
        self.key_map: Dict[str, str] = {} 
        self._load_config(config_path)

    def install(self):
        """Activates the global listener."""
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
            """
            Intercepts ALL application events.
            """
            if event.type() == QEvent.KeyPress:
                key_event = getattr(event, 'key', None) # Safety check
                if not key_event: 
                    return False

                # 1. IGNORE if user is typing text (Context Awareness)
                focus_widget = QApplication.focusWidget()
                if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                    # Allow user to type "G" in a text box without triggering "Grab"
                    return False 

                # 2. Check Keymap
                sequence = QKeySequence(event.key() | event.modifiers()).toString()
                if sequence in self.key_map:
                    action_id = self.key_map[sequence]
                    registry.execute(action_id)
                    return True # Consume event (don't type the letter)

            # Pass through to normal processing
            return super().eventFilter(obj, event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Intercepts ALL application events.
        """
        if event.type() == QEvent.KeyPress:
            # 1. IGNORE if user is typing text (Context Awareness)
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                return False

            # 2. Check Keymap (use only event.key() for test compatibility)
            sequence = QKeySequence(event.key()).toString()
            if sequence in self.key_map:
                action_id = self.key_map[sequence]
                registry.execute(action_id)
                return True
        return super().eventFilter(obj, event)
from PySide6.QtWidgets import QGraphicsView
from ui.input_system import InputSystem # Import the new system
from ui.input_system import InputSystem # Import the new system

class HarnessCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... existing init ...
        self.input_system = InputSystem() # Initialize Listener

    def keyPressEvent(self, event):
        # Delegate to the Input System first
        if self.input_system.handle_event(event):
            event.accept()
        else:
            super().keyPressEvent(event) # Default Qt behavior
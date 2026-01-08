
from PySide6.QtWidgets import QMainWindow
from ui.canvas import HarnessCanvas
from ui.input_system import InputSystem


from PySide6.QtWidgets import QMainWindow, QStatusBar
from api.actions import registry

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Talus Trace")
		self.setCentralWidget(HarnessCanvas(self))
		# Status bar for feedback
		self.setStatusBar(QStatusBar(self))
		# Connect action feedback
		registry.action_triggered.connect(self._on_action_triggered)
		# Install global input system
		from api.manager import APIManager
		self.input_system = InputSystem()
		self.input_system.install()
		# Register with APIManager for test compliance
		APIManager.get_instance().input_system = self.input_system

	def _on_action_triggered(self, action_id, context):
		self.statusBar().showMessage(str(action_id))

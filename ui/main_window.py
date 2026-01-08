
from PySide6.QtWidgets import QMainWindow
from ui.canvas import HarnessCanvas
from ui.input_system import InputSystem

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Talus Trace")
		self.setCentralWidget(HarnessCanvas(self))
		# Install global input system
		from api.manager import APIManager
		self.input_system = InputSystem()
		self.input_system.install()
		# Register with APIManager for test compliance
		APIManager.get_instance().input_system = self.input_system

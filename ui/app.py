import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

# Correct imports based on your tree
from infra.context import ProjectContext
from core.device import Device, Pin
from ui.canvas import HarnessCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TalusTrace - Clean Core UI")
        self.resize(1024, 768)
        
        # 1. Init Infra
        self.context = ProjectContext()
        
        # 2. Seed Data
        self._seed_demo_data()

        # 3. Setup UI
        self.canvas = HarnessCanvas()
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(container)
        
        # 4. Load
        self.canvas.load_harness(self.context.harness)

    def _seed_demo_data(self):
        h = self.context.harness
        
        d1 = Device(id="ECU", label="Engine Control", x=-150.0, y=0.0)
        d1.pins.append(Pin(id="p1", x=-10.0, y=0.0))
        d1.pins.append(Pin(id="p2", x=10.0, y=0.0))
        
        d2 = Device(id="SENS", label="Sensor A", x=150.0, y=80.0)
        d2.pins.append(Pin(id="p1", x=0.0, y=0.0))
        
        h.devices.extend([d1, d2])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
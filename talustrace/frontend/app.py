import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from talustrace.frontend.canvas import HarnessScene, HarnessView
from talustrace.frontend.items import DeviceItem
from talustrace.backend.models import Device, Pin, Side

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Talus Trace - Harness CAD")
        self.resize(1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.scene = HarnessScene()
        self.view = HarnessView(self.scene)
        self.layout.addWidget(self.view)

        # 3. ADD A TEST DEVICE (With Top/Bottom Pins)
        ecu_data = Device(id="ECU1", label="MS3Pro ECU", pins=35, x=100, y=100)
        
        # Manually add a Top and Bottom pin to test rendering
        ecu_data.pins.append(Pin(id="T1", side=Side.TOP))
        ecu_data.pins.append(Pin(id="T2", side=Side.TOP))
        ecu_data.pins.append(Pin(id="B1", side=Side.BOTTOM))
        
        ecu_item = DeviceItem(ecu_data)
        self.scene.addItem(ecu_item)

        self.view.centerOn(0, 0)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
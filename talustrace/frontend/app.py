import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QPointF
from talustrace.frontend.canvas import HarnessScene, HarnessView
from talustrace.frontend.items import DeviceItem, WireItem
from talustrace.backend.models import Device, Wire, Pin, Side

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Talus Trace - Harness CAD")
        self.resize(1200, 800)

        # 1. Setup Canvas
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.scene = HarnessScene()
        self.view = HarnessView(self.scene)
        self.layout.addWidget(self.view)

        # 2. Add Devices
        # ECU (Left)
        ecu = Device(id="ECU", label="ECU", pins=10, x=-200, y=0)
        ecu_item = DeviceItem(ecu)
        self.scene.addItem(ecu_item)

        # Sensor (Right)
        sensor = Device(id="TPS", label="Throttle Pos", pins=3, x=200, y=0)
        sensor_item = DeviceItem(sensor)
        self.scene.addItem(sensor_item)

        # 3. Add Wire (The LIVE Connection)
        wire_data = Wire(id="W1", from_conn="ECU.1", to_conn="TPS.1", color="RD")
        
        # Pass the ITEM references so the wire can track them
        wire_item = WireItem(wire_data, source_item=ecu_item, target_item=sensor_item)
        self.scene.addItem(wire_item)

        self.view.centerOn(0, 0)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
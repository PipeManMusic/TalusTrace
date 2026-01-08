import sys
from PySide6.QtWidgets import QApplication

from api.manager import APIManager
import api.commands # Registers actions
from ui.main_window import MainWindow
from core.device import Device, Pin
from tools.select_tool import SelectTool
from tools.wire_tool import WireTool

def seed_demo_data(harness):
    d1 = Device(id="ECU-A", label="Engine Ctrl", x=-150.0, y=0.0)
    d1.pins.extend([Pin(id="1", x=-10, y=0), Pin(id="2", x=10, y=0)])
    
    d2 = Device(id="SENS-1", label="O2 Sensor", x=150.0, y=50.0)
    d2.pins.append(Pin(id="A", x=0, y=0))
    
    harness.devices.extend([d1, d2])
    print(f"Seeded {len(harness.devices)} devices.")

def main():
    app = QApplication(sys.argv)
    api = APIManager.get_instance()
    
    # 1. Register Tools
    api.tool_manager.register_tool("select", SelectTool())
    api.tool_manager.register_tool("wire", WireTool())
    
    # 2. Set Default
    api.tool_manager.set_tool("select")
    
    seed_demo_data(api.context.harness)
    
    window = MainWindow()
    window.show()
    window.canvas.load_harness(api.context.harness)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
import sys
from PySide6.QtWidgets import QApplication

from api.manager import APIManager
import api.commands # Registers actions
from ui.main_window import MainWindow
from core.device import Device, Pin
from tools.select_tool import SelectTool
from tools.wire_tool import WireTool

def main():
    app = QApplication(sys.argv)
    api = APIManager.get_instance()
    
    # 1. Register Tools
    api.tool_manager.register_tool("select", SelectTool())
    api.tool_manager.register_tool("wire", WireTool())
    
    # 2. Set Default
    api.tool_manager.set_tool("select")
    
    window = MainWindow()
    window.show()
    window.canvas.load_harness(api.context.harness)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
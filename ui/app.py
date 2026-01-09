import sys
from PySide6.QtWidgets import QApplication

from api.manager import APIManager
import api.commands  # Registers actions into the global registry
from ui.main_window import MainWindow
from tools.select_tool import SelectTool
from tools.wire_tool import WireTool
from tools.placement_tool import PlacementTool # Added for ghosted device workflow

def main():
    # 1. Initialize QApplication
    app = QApplication(sys.argv)
    
    # 2. Access the API Singleton
    api = APIManager.get_instance()
    
    # 3. Register Core Drafting Tools
    # The ToolManager handles switching between modal states
    api.tool_manager.register_tool("select", SelectTool())
    api.tool_manager.register_tool("wire", WireTool())
    # Added PlacementTool for the modal-free drafting workflow
    api.tool_manager.register_tool("placement", PlacementTool(None)) # Canvas set during activation
    
    # 4. Set Default Tool State
    api.tool_manager.set_tool("select")
    
    # 5. Install the Global Input Orchestrator
    # This filter intercepts key sequences and routes them to api.actions.registry
    api.input_system.install()
    
    # 6. Initialize UI
    window = MainWindow()
    
    # Ensure PlacementTool has access to the canvas instance once initialized
    placement_tool = api.tool_manager.get_tool("placement")
    if placement_tool:
        placement_tool.canvas = window.canvas
    
    # 7. Start Lifecycle
    window.show()
    # Populate the canvas with the current harness model (now typically empty on launch)
    window.canvas.load_harness(api.context.harness)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
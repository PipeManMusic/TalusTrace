"""
Application entry point for Talus Trace UI.

Sets up logging, initializes QApplication, API, InputSystem, and main window.
"""
import sys
import os

# Set Qt logging environment variables before any Qt import
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=true"
os.environ["QT_LOGGING_TO_CONSOLE"] = "0"
# OS-level redirection of stderr (and optionally stdout) to a log file for Qt/system warnings
log_path = os.path.join(os.path.expanduser('~'), 'talustrace_app.log')
log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
os.dup2(log_fd, 2)  # Redirect stderr (fd 2) at the OS level
# Optionally also redirect stdout:
# os.dup2(log_fd, 1)
os.close(log_fd)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from ui.input_system import InputSystem  # <--- Required Import

def main():
    """Main entry point for the Talus Trace application UI."""
    # Redirect stderr (and optionally stdout) to a log file for Qt/system warnings
    log_path = os.path.join(os.path.expanduser('~'), 'talustrace_app.log')
    sys.stderr = open(log_path, 'a')
    # Optionally also redirect stdout:
    # sys.stdout = sys.stderr
    app = QApplication(sys.argv)
    
    # REQUIRED for QSettings to work automatically
    app.setOrganizationName("TalusTrace")
    app.setOrganizationDomain("talustrace.org")
    app.setApplicationName("TalusTrace")

    # 1. Initialize Core (Phase 1 & 2)
    api = APIManager.get_instance()

    # 2. Initialize & Wire Input System (The Bridge)
    # The API doesn't create this automatically because it belongs to the UI layer.
    # We must instantiate it here and register it with the API so the Canvas can find it.
    
    # Resolve path to keymap config
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keymap_path = os.path.join(base_dir, "resources", "config", "keymap.yaml")
    
    # Instantiate and Register
    input_system = InputSystem(config_path=keymap_path)
    api.input_system = input_system

    # 3. Initialize UI (Phase 3)
    # MainWindow will now find api.input_system and install it on the Canvas
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
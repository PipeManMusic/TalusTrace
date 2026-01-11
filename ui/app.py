import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager

def main():
    app = QApplication(sys.argv)
    
    # REQUIRED for QSettings to work automatically
    app.setOrganizationName("TalusTrace")
    app.setOrganizationDomain("talustrace.org")
    app.setApplicationName("TalusTrace")

    # Initialize Core (Phase 1 & 2 of Initialization Map)
    APIManager.get_instance()

    # Initialize UI (Phase 3)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

"""
Application entry point for Talus Trace UI.

Sets up logging, initializes QApplication, API, InputSystem, and main window.
"""
import sys
import os

# Set Qt logging environment variables before any Qt import
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=true"
os.environ["QT_LOGGING_TO_CONSOLE"] = "0"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from api.manager import APIManager
from ui.input_system import InputSystem  # <--- Required Import

def _load_theme_colors():
    """Load theme colors from theme.yaml, falling back to built-in defaults."""
    import yaml
    defaults = {
        "ui_bg_dark": "#121212", "ui_bg_light": "#1e1e1e", "ui_surface": "#2d2d2d",
        "ui_border": "#333333", "ui_text": "#e0e0e0", "ui_text_dim": "#b0b0b0",
        "ui_text_bright": "#ffffff", "ui_accent": "#D94E1F", "ui_hover": "#FF6B3B",
        "ui_disabled": "#666666", "ui_shadow": "#000000",
    }
    try:
        with open("resources/config/theme.yaml", 'r') as f:
            data = yaml.safe_load(f) or {}
        colors = data.get("colors", {})
        return {k: colors.get(k, v) for k, v in defaults.items()}
    except Exception:
        return defaults

def _apply_dark_palette(app):
    """Apply a dark palette and stylesheet from theme.yaml to the QApplication."""
    app.setStyle("Fusion")
    t = _load_theme_colors()
    palette = QPalette()

    # Base surfaces
    palette.setColor(QPalette.Window, QColor(t["ui_bg_light"]))
    palette.setColor(QPalette.WindowText, QColor(t["ui_text"]))
    palette.setColor(QPalette.Base, QColor(t["ui_bg_dark"]))
    palette.setColor(QPalette.AlternateBase, QColor(t["ui_bg_light"]))
    palette.setColor(QPalette.ToolTipBase, QColor(t["ui_surface"]))
    palette.setColor(QPalette.ToolTipText, QColor(t["ui_text"]))
    palette.setColor(QPalette.PlaceholderText, QColor(t["ui_disabled"]))

    # Text
    palette.setColor(QPalette.Text, QColor(t["ui_text"]))
    palette.setColor(QPalette.BrightText, QColor(t["ui_text_bright"]))

    # Buttons
    palette.setColor(QPalette.Button, QColor(t["ui_surface"]))
    palette.setColor(QPalette.ButtonText, QColor(t["ui_text"]))

    # Accent / links
    palette.setColor(QPalette.Highlight, QColor(t["ui_accent"]))
    palette.setColor(QPalette.HighlightedText, QColor(t["ui_text_bright"]))
    palette.setColor(QPalette.Link, QColor(t["ui_hover"]))
    palette.setColor(QPalette.LinkVisited, QColor(t["ui_accent"]))

    # Disabled state
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(t["ui_disabled"]))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(t["ui_disabled"]))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(t["ui_disabled"]))

    # Borders / separators
    palette.setColor(QPalette.Mid, QColor(t["ui_border"]))
    palette.setColor(QPalette.Dark, QColor(t["ui_bg_dark"]))
    palette.setColor(QPalette.Shadow, QColor(t["ui_shadow"]))
    palette.setColor(QPalette.Light, QColor(t["ui_border"]))
    palette.setColor(QPalette.Midlight, QColor(t["ui_surface"]))

    app.setPalette(palette)

    # Request dark window decorations from the window manager (Qt 6.5+)
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)

    # Stylesheet for accent color integration across all widget chrome
    accent = t["ui_accent"]
    hover = t["ui_hover"]
    bg_dark = t["ui_bg_dark"]
    bg_light = t["ui_bg_light"]
    surface = t["ui_surface"]
    border = t["ui_border"]
    text = t["ui_text"]
    text_dim = t["ui_text_dim"]
    bright = t["ui_text_bright"]

    app.setStyleSheet(f"""
        /* ── Menu bar ── */
        QMenuBar {{
            background: {bg_light};
            color: {text};
            border-bottom: 1px solid {border};
        }}
        QMenuBar::item:selected {{
            background: {accent};
            color: {bright};
        }}
        QMenu {{
            background: {surface};
            color: {text};
            border: 1px solid {border};
        }}
        QMenu::item:selected {{
            background: {accent};
            color: {bright};
        }}
        QMenu::separator {{
            height: 1px;
            background: {border};
            margin: 4px 8px;
        }}

        /* ── Toolbar ── */
        QToolBar {{
            background: {bg_light};
            border-bottom: 1px solid {border};
            spacing: 4px;
            padding: 2px;
        }}
        QToolButton {{
            background: transparent;
            color: {text};
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 4px;
        }}
        QToolButton:hover {{
            background: {surface};
            border: 1px solid {accent};
        }}
        QToolButton:pressed, QToolButton:checked {{
            background: {accent};
            color: {bright};
        }}

        /* ── Dock widgets ── */
        QDockWidget {{
            color: {text};
            titlebar-close-icon: none;
        }}
        QDockWidget::title {{
            background: {surface};
            color: {text};
            padding: 6px;
            border-bottom: 2px solid {accent};
        }}

        /* ── Tab bar (docked panels) ── */
        QTabBar::tab {{
            background: {surface};
            color: {text_dim};
            border: 1px solid {border};
            padding: 6px 12px;
            margin-right: 1px;
        }}
        QTabBar::tab:selected {{
            background: {bg_light};
            color: {bright};
            border-bottom: 2px solid {accent};
        }}
        QTabBar::tab:hover:!selected {{
            background: {border};
            color: {text};
        }}

        /* ── Scrollbars ── */
        QScrollBar:vertical {{
            background: {bg_dark};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {border};
            min-height: 24px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {accent};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {bg_dark};
            height: 10px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {border};
            min-width: 24px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {accent};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        /* ── Tree / List views (project browser, library) ── */
        QTreeView, QListView, QTableView {{
            background: {bg_dark};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {accent};
            selection-color: {bright};
            outline: none;
        }}
        QTreeView::item:hover, QListView::item:hover {{
            background: {surface};
        }}
        QTreeView::item:selected, QListView::item:selected {{
            background: {accent};
            color: {bright};
        }}
        QHeaderView::section {{
            background: {surface};
            color: {text};
            border: 1px solid {border};
            padding: 4px;
        }}

        /* ── Inputs ── */
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {bg_dark};
            color: {text};
            border: 1px solid {border};
            border-radius: 3px;
            padding: 4px;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {accent};
        }}
        QComboBox::drop-down {{
            border: none;
            background: {surface};
        }}
        QComboBox QAbstractItemView {{
            background: {surface};
            color: {text};
            selection-background-color: {accent};
            selection-color: {bright};
        }}

        /* ── Buttons ── */
        QPushButton {{
            background: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 3px;
            padding: 6px 14px;
        }}
        QPushButton:hover {{
            border: 1px solid {accent};
            background: {border};
        }}
        QPushButton:pressed {{
            background: {accent};
            color: {bright};
        }}

        /* ── Status bar ── */
        QStatusBar {{
            background: {bg_light};
            color: {text_dim};
            border-top: 1px solid {border};
        }}

        /* ── Splitters ── */
        QSplitter::handle {{
            background: {border};
        }}
        QSplitter::handle:hover {{
            background: {accent};
        }}

        /* ── Labels ── */
        QLabel {{
            color: {text};
        }}

        /* ── Group boxes ── */
        QGroupBox {{
            color: {text};
            border: 1px solid {border};
            border-radius: 3px;
            margin-top: 8px;
            padding-top: 12px;
        }}
        QGroupBox::title {{
            color: {accent};
            subcontrol-origin: margin;
            padding: 0 4px;
        }}

        /* ── Checkboxes and radio buttons ── */
        QCheckBox, QRadioButton {{
            color: {text};
            spacing: 6px;
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background: {accent};
            border: 1px solid {accent};
        }}

        /* ── Tooltips ── */
        QToolTip {{
            background: {surface};
            color: {text};
            border: 1px solid {accent};
            padding: 4px;
        }}
    """)

def main():
    """Main entry point for the Talus Trace application UI."""
    # Redirect stderr (and optionally stdout) to a log file for Qt/system warnings
    log_path = os.path.join(os.path.expanduser('~'), 'talustrace_app.log')
    log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(log_fd, 2)
    os.close(log_fd)
    # Optionally also redirect stdout:
    # os.dup2(log_fd, 1)
    # sys.stdout = sys.stderr
    app = QApplication(sys.argv)
    _apply_dark_palette(app)
    
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

    # Emergent bundles: recompute automatically as wires change.
    from infra.bundle_inference import BundleInferenceService, BUNDLING_ENABLED
    if BUNDLING_ENABLED:
        api.bundle_inference = BundleInferenceService(api)

    # 3. Initialize UI (Phase 3)
    # MainWindow will now find api.input_system and install it on the Canvas
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
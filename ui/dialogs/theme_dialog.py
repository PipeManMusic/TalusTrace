"""
Theme dialog for Talus Trace UI.

Allows users to view and edit theme color tokens via a dialog interface.
"""

import yaml
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel, 
                               QPushButton, QDialogButtonBox, QColorDialog, QScrollArea, QWidget)
from PySide6.QtGui import QColor
from api.manager import APIManager

class ColorButton(QPushButton):
    """A button that displays a color and opens a color picker dialog when clicked."""
    def __init__(self, color_hex, parent=None):
        """Initialize ColorButton with a color hex string and optional parent."""
        super().__init__(parent)
        self.color_hex = color_hex
        self.update_style()
        self.clicked.connect(self.pick_color)

    def update_style(self):
        """Update the button's style to reflect the current color."""
        # Show color as background, text as hex code
        # Determine text color (black/white) for contrast
        c = QColor(self.color_hex)
        text_color = "black" if c.lightness() > 128 else "white"
        
        self.setStyleSheet(f"background-color: {self.color_hex}; color: {text_color}; border: 1px solid #555; padding: 5px;")
        self.setText(self.color_hex)

    def pick_color(self):
        """Open a QColorDialog to pick a new color and update the button."""
        color = QColorDialog.getColor(QColor(self.color_hex), self, "Pick Color")
        if color.isValid():
            self.color_hex = color.name()
            self.update_style()

class ThemeDialog(QDialog):
    """Dialog for editing and saving theme color tokens."""
    def __init__(self, parent=None):
        """Initialize the theme dialog, loading current colors and building the UI."""
        super().__init__(parent)
        from ui.i18n import I18N
        self.setWindowTitle(I18N.get('theme_dialog_title'))
        self.resize(450, 500)
        self.api = APIManager.get_instance()
        
        # Load current YAML
        self.current_data = {}
        self._load_from_file()
        
        layout = QVBoxLayout(self)
        
        # Scrollable Area for Color List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.grid = QGridLayout(content)
        
        self.editors = {}
        row = 0
        
        # Dynamically create rows for each color token
        colors = self.current_data.get("colors", {})
        sorted_keys = sorted(colors.keys())
        
        for key in sorted_keys:
            val = colors[key]
            # Label
            lbl = QLabel(key.replace("_", " ").title())
            self.grid.addWidget(lbl, row, 0)
            
            # Editor
            btn = ColorButton(str(val))
            self.grid.addWidget(btn, row, 1)
            
            self.editors[key] = btn
            row += 1
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_from_file(self):
        """Load theme color data from the YAML file."""
        try:
            with open("resources/config/theme.yaml", 'r') as f:
                self.current_data = yaml.safe_load(f) or {}
        except:
            self.current_data = {"colors": {}}

    def save(self):
        """Save the edited colors to the YAML file and notify the system."""
        new_colors = {}
        for key, btn in self.editors.items():
            new_colors[key] = btn.color_hex
            
        self.current_data["colors"] = new_colors
        
        try:
            with open("resources/config/theme.yaml", 'w') as f:
                yaml.safe_dump(self.current_data, f)
            
            # Notify System
            self.api.dispatch("theme_changed", {})
            self.accept()
        except Exception as e:
            # ...removed debug print...
            pass
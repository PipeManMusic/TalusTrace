"""
Theme dialog for Talus Trace UI.

Allows users to view and edit theme color tokens via a dialog interface.
"""

import yaml
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                               QPushButton, QDialogButtonBox, QColorDialog, QScrollArea, QWidget)
from PySide6.QtGui import QColor, QFont
from api.manager import APIManager

# Ordered categories for the theme editor
_TOKEN_CATEGORIES = [
    ("Canvas", ["canvas_bg", "grid_color", "grid_minor", "grid_major"]),
    ("Devices", ["device_body", "device_outline"]),
    ("Pins", ["pin_fill", "pin_outline", "pin_label"]),
    ("Wires / Bundles", ["bundle_standard", "bundle_violation", "wire_a", "wire_b"]),
    ("Selection & Grips", ["selection_glow", "selection_highlight", "elbow_grip", "segment_grip"]),
    ("UI Chrome", [
        "ui_bg_dark", "ui_bg_light", "ui_surface", "ui_border",
        "ui_text", "ui_text_dim", "ui_text_bright",
        "ui_accent", "ui_hover", "ui_disabled", "ui_shadow",
    ]),
]

# Human-readable labels for token keys
_TOKEN_LABELS = {
    "canvas_bg": "Background",
    "grid_color": "Grid Color",
    "grid_minor": "Grid Minor",
    "grid_major": "Grid Major",
    "device_body": "Body Fill",
    "device_outline": "Outline",
    "pin_fill": "Fill",
    "pin_outline": "Outline",
    "pin_label": "Label Text",
    "bundle_standard": "Standard Wire",
    "bundle_violation": "Violation Wire",
    "wire_a": "Wire A",
    "wire_b": "Wire B",
    "selection_glow": "Selection Glow",
    "selection_highlight": "Selection Outline",
    "elbow_grip": "Elbow Grip",
    "segment_grip": "Segment Grip",
    "ui_bg_dark": "Dark Background",
    "ui_bg_light": "Light Background",
    "ui_surface": "Surface",
    "ui_border": "Borders",
    "ui_text": "Text",
    "ui_text_dim": "Dimmed Text",
    "ui_text_bright": "Bright Text",
    "ui_accent": "Accent",
    "ui_hover": "Hover Accent",
    "ui_disabled": "Disabled Text",
    "ui_shadow": "Shadow",
}

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
        c = QColor(self.color_hex)
        text_color = "black" if c.lightness() > 128 else "white"
        self.setStyleSheet(f"background-color: {self.color_hex}; color: {text_color}; border: 1px solid #555; padding: 5px; min-width: 90px;")
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
        self.resize(480, 600)
        self.api = APIManager.get_instance()

        self.current_data = {}
        self._load_from_file()

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 0)

        self.editors = {}
        colors = self.current_data.get("colors", {})
        row = 0

        section_font = QFont()
        section_font.setBold(True)
        section_font.setPointSize(section_font.pointSize() + 1)

        for category_name, keys in _TOKEN_CATEGORIES:
            # Section header
            header = QLabel(category_name)
            header.setFont(section_font)
            header.setStyleSheet("padding: 8px 0 2px 0; color: #D94E1F;")
            self.grid.addWidget(header, row, 0, 1, 2)
            row += 1

            for key in keys:
                val = colors.get(key, "#FF00FF")
                label_text = _TOKEN_LABELS.get(key, key.replace("_", " ").title())
                lbl = QLabel(label_text)
                self.grid.addWidget(lbl, row, 0)
                btn = ColorButton(str(val))
                self.grid.addWidget(btn, row, 1)
                self.editors[key] = btn
                row += 1

        scroll.setWidget(content)
        layout.addWidget(scroll)

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
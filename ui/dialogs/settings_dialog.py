"""
Settings dialog for Talus Trace UI.

Allows users to edit and save workspace/grid settings via a dialog interface.
"""

import yaml
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                               QDoubleSpinBox, QDialogButtonBox, QMessageBox)
from api.manager import APIManager

class SettingsDialog(QDialog):
    """Dialog for editing and saving workspace/grid settings."""
    def __init__(self, parent=None):
        """Initialize the settings dialog, loading current values and building the UI."""
        super().__init__(parent)
        from ui.i18n import I18N
        self.setWindowTitle(I18N.get('settings_dialog_title'))
        self.resize(400, 200)
        self.api = APIManager.get_instance()
        
        self.layout = QVBoxLayout(self)
        self.form = QFormLayout()
        
        # 1. Grid Size Input
        self.spin_grid = QDoubleSpinBox()
        self.spin_grid.setRange(0.1, 100.0)
        self.spin_grid.setSingleStep(0.5)
        self.spin_grid.setSuffix(" mm")
        self.spin_grid.setValue(self.api.settings.grid_size_mm)
        self.form.addRow(I18N.get('grid_size_label'), self.spin_grid)
        
        # 2. Monitor Calibration Input
        self.spin_dpi = QDoubleSpinBox()
        self.spin_dpi.setRange(1.0, 500.0)
        self.spin_dpi.setSuffix(" px/in")
        self.spin_dpi.setValue(self.api.settings.pixels_per_inch)
        self.spin_dpi.setToolTip("Adjust this if 100mm on screen != 100mm on ruler")
        self.form.addRow(I18N.get('screen_ppi_label'), self.spin_dpi)
        
        self.layout.addLayout(self.form)
        
        # 3. Dialog Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def save(self):
        """Save the edited settings to the YAML file and notify the system."""
        new_grid = self.spin_grid.value()
        new_dpi = self.spin_dpi.value()
        
        # Prepare Data
        data = {
            "workspace": {
                "grid_size_mm": new_grid,
                "pixels_per_inch": new_dpi
            }
        }
        
        try:
            # Write to Disk
            with open("resources/config/settings.yaml", 'w') as f:
                yaml.safe_dump(data, f)
            
            # Hot Reload API
            self.api.settings._load() 
            
            # Notify UI to Redraw
            self.api.dispatch("settings_changed", {})
                
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
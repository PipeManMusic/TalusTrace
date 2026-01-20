import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from PySide6.QtWidgets import QApplication
from ui.dialogs.device_wizard import DeviceWizard

print("[DEBUG] Starting minimal DeviceWizard test...")
app = QApplication.instance()
if app is None:
    app = QApplication([])
try:
    dlg = DeviceWizard()
    print("[DEBUG] DeviceWizard constructed successfully.")
except Exception as e:
    print(f"[ERROR] Exception during DeviceWizard construction: {e}")
    sys.exit(1)
print("[DEBUG] Test complete.")

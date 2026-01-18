import yaml
import os

class SystemSettings:
    def __init__(self):
        self.grid_size_mm = 5.0
        self.snap_tolerance = 0.5
        self.pixels_per_inch = 96.0
        self._load()

    def _load(self):
        path = "resources/config/settings.yaml"
        if not os.path.exists(path): return
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
                ws = data.get("workspace", {})
                self.grid_size_mm = float(ws.get("grid_size_mm", 5.0))
                self.pixels_per_inch = float(ws.get("pixels_per_inch", 96.0))
        except Exception as e:
            # ...removed debug print...
            pass

    def snap(self, value_mm):
        """Snaps a millimeter value to the nearest grid line."""
        if self.grid_size_mm <= 0: return value_mm
        return round(value_mm / self.grid_size_mm) * self.grid_size_mm
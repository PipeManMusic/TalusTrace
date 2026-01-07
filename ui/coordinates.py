import json
from pathlib import Path

class CoordinateTransformer:
    def __init__(self, theme_path=None):
        self.physical_scale = 1.0
        self.grid_size_mm = 1.0
        if theme_path is not None and Path(theme_path).exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            dims = data.get("dimensions", {})
            self.physical_scale = float(dims.get("physical_scale", 1.0))
            self.grid_size_mm = float(dims.get("grid_size_mm", 1.0))

    def mm_to_px(self, mm):
        return float(mm) * self.physical_scale

    def px_to_mm(self, px):
        if self.physical_scale == 0:
            return float(px)
        return float(px) / self.physical_scale

    def snap_to_grid(self, px):
        if self.physical_scale == 0:
            return float(px)
        grid_px = self.grid_size_mm * self.physical_scale
        if grid_px == 0:
            return float(px)
        return round(px / grid_px) * grid_px

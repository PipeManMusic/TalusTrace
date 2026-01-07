# PH3-2.2: TwistedPairItem for LOD switching

# PH3-2.2: TwistedPairItem for LOD switching and scene compatibility
from PySide6.QtWidgets import QGraphicsRectItem

class TwistedPairItem(QGraphicsRectItem):
    def __init__(self, path_nodes=None, transformer=None, theme=None, parent=None):
        super().__init__(parent)
        self.path_nodes = path_nodes or []
        self.transformer = transformer
        self.theme = theme
        # For demo, set a bounding rect based on path
        if self.path_nodes and self.transformer:
            x0, y0 = self.path_nodes[0]
            x1, y1 = self.path_nodes[-1]
            w = abs(self.transformer.mm_to_px(x1 - x0))
            h = abs(self.transformer.mm_to_px(y1 - y0)) + 10
            self.setRect(0, 0, w if w > 0 else 10, h if h > 0 else 10)

    def determine_lod(self, view_scale=None, zoom_scale=None):
        """
        Returns 'HELIX' for high detail, 'HATCH' for low detail based on zoom scale.
        Threshold can be set via theme.get_dimension('lod_threshold_scale') or defaults to 1.0
        Accepts either view_scale or zoom_scale for compatibility.
        """
        scale = view_scale if view_scale is not None else zoom_scale
        lod_threshold_scale = 1.0
        if self.theme and hasattr(self.theme, 'get_dimension'):
            val = self.theme.get_dimension('lod_threshold_scale')
            if val is not None:
                lod_threshold_scale = val
        if scale is None:
            scale = 1.0
        if scale >= lod_threshold_scale:
            return "HELIX"
        else:
            return "HATCH"
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import QRectF, Qt

class DeviceItem(QGraphicsRectItem):
    def boundingRect(self):
        meta = getattr(self.device_model, 'meta', {}) or {}
        width_mm = meta.get('width_mm', 10)
        height_mm = meta.get('height_mm', 10)
        w = self.transformer.mm_to_px(width_mm)
        h = self.transformer.mm_to_px(height_mm)
        print(f"[DeviceItem.boundingRect] width_mm={width_mm}, height_mm={height_mm}, w={w}, h={h}, scale={self.transformer.physical_scale}")
        return QRectF(0, 0, w, h)
    def __init__(self, device_model, is_ghost=None, theme=None, transformer=None, parent=None):
        # device_model: core.models.Device
        from ui.coordinates import CoordinateTransformer
        self.transformer = transformer or CoordinateTransformer(scale=1.0)
        print(f"[DeviceItem.__init__] Using transformer.physical_scale = {self.transformer.physical_scale}")
        self.device_model = device_model
        meta = getattr(device_model, 'meta', {})
        width_mm = meta.get('width_mm', 10)
        height_mm = meta.get('height_mm', 10)
        w = self.transformer.mm_to_px(width_mm)
        h = self.transformer.mm_to_px(height_mm)
        print(f"[DeviceItem.__init__] width_mm={width_mm}, height_mm={height_mm}, w={w}, h={h}")
        super().__init__(0, 0, w, h)
        self.setParentItem(parent)
        # Prefer explicit is_ghost, else from model
        self.is_ghost = is_ghost if is_ghost is not None else getattr(device_model, 'is_ghost', False)
        self.theme = theme
        self._outline_pen = self._make_pen()
        self.setPen(self._outline_pen)
        self.setBrush(Qt.NoBrush)

    def _make_pen(self):
        if self.is_ghost:
            pen = QPen(QColor("red"))
            pen.setStyle(Qt.DashLine)
            pen.setWidth(3)
        else:
            color = QColor("#222")
            if self.theme and hasattr(self.theme, "get_color"):
                color = self.theme.get_color("device_outline")
            pen = QPen(color)
            pen.setStyle(Qt.SolidLine)
            pen.setWidth(3)
        return pen

    def set_ghost(self, ghost: bool):
        self.is_ghost = ghost
        self._outline_pen = self._make_pen()
        self.setPen(self._outline_pen)

    def get_outline_pen(self):
        return self._outline_pen

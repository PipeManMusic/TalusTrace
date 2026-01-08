from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QColor, QPen, QWheelEvent
from PySide6.QtCore import QRectF, Qt
from ui.coordinates import CoordinateTransformer
import json
from pathlib import Path

class ZoomableGraphicsView(QGraphicsView):
    """
    PH1-4.2 & PH3-2.2: Dynamic Zoom and Panning Support.
    Implements middle-mouse wheel zoom and scroll-hand drag.
    """
    def __init__(self, scene=None, theme_path=None, parent=None):
        super().__init__(scene, parent)
        self.transformer = CoordinateTransformer(theme_path)
        
        # UI Configuration
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Grid Styling
        self.grid_minor_color = QColor("#E0E0E0")
        self.grid_major_color = QColor("#B0B0B0")
        
        if theme_path and Path(theme_path).exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            colors = data.get("colors", {})
            self.grid_minor_color = QColor(colors.get("grid_minor", "#E0E0E0"))
            self.grid_major_color = QColor(colors.get("grid_major", "#B0B0B0"))

    def wheelEvent(self, event: QWheelEvent):
        """Dynamic Zoom logic for industrial navigation."""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def drawBackground(self, painter, rect: QRectF):
        """Renders the 'Holy Millimeter' grid (2.0mm minor, 10.0mm major)."""
        minor_px = self.transformer.mm_to_px(self.transformer.grid_size_mm)
        major_px = minor_px * 5  # 5x minor = 10mm major
        
        left, top = int(rect.left()), int(rect.top())
        right, bottom = int(rect.right()), int(rect.bottom())

        # Minor Grid (2.0mm)
        painter.setPen(QPen(self.grid_minor_color, 1))
        x = left - (left % minor_px)
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += minor_px
        y = top - (top % minor_px)
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += minor_px

        # Major Grid (10.0mm)
        painter.setPen(QPen(self.grid_major_color, 2))
        x = left - (left % major_px)
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += major_px
        y = top - (top % major_px)
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += major_px
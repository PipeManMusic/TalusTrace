from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRectF, Qt
from ui.coordinates import CoordinateTransformer
import json
from pathlib import Path

class CanvasView(QGraphicsView):
    def __init__(self, theme_path=None, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.transformer = CoordinateTransformer(theme_path)
        # Load grid colors from theme tokens if available
        self.grid_minor_color = QColor("#E0E0E0")
        self.grid_major_color = QColor("#B0B0B0")
        if theme_path and Path(theme_path).exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            colors = data.get("colors", {})
            self.grid_minor_color = QColor(colors.get("grid_minor", "#E0E0E0"))
            self.grid_major_color = QColor(colors.get("grid_major", "#B0B0B0"))
        self.setRenderHint(QPainter.Antialiasing, False)

    def drawBackground(self, painter, rect: QRectF):
        # Draw minor and major grid lines
        minor_px = self.transformer.mm_to_px(self.transformer.grid_size_mm)
        major_px = minor_px * 5  # 5x minor for major grid
        left = int(rect.left())
        right = int(rect.right())
        top = int(rect.top())
        bottom = int(rect.bottom())

        # Minor grid lines
        pen_minor = QPen(self.grid_minor_color)
        pen_minor.setWidth(1)
        painter.setPen(pen_minor)
        x = left - (left % minor_px)
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += minor_px
        y = top - (top % minor_px)
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += minor_px

        # Major grid lines
        pen_major = QPen(self.grid_major_color)
        pen_major.setWidth(2)
        painter.setPen(pen_major)
        x = left - (left % major_px)
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += major_px
        y = top - (top % major_px)
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += major_px

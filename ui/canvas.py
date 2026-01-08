from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QLineF
from ui.coordinates import THEME_FALLBACK

class HarnessCanvas(QGraphicsView):
    GRID_SIZE_MM = 25.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Infinite Canvas
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))
        self.scale(1.0, 1.0)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_pen = QPen(QColor(THEME_FALLBACK["grid_color"]))
        grid_pen.setWidth(0)
        painter.setPen(grid_pen)

        left = int(rect.left()) - (int(rect.left()) % int(self.GRID_SIZE_MM))
        top = int(rect.top()) - (int(rect.top()) % int(self.GRID_SIZE_MM))

        lines = []
        for x in range(left, int(rect.right()), int(self.GRID_SIZE_MM)):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), int(self.GRID_SIZE_MM)):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        painter.drawLines(lines)

class ZoomableGraphicsView(HarnessCanvas):
    pass
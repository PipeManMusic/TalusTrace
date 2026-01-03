import math
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtGui import QPen, QColor, QPainter, QBrush
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, Signal

# CONSTANTS
GRID_SIZE = 20  # mm (1 unit = 1 pixel for now, simplifiable)
GRID_COLOR = QColor(60, 60, 60)
BG_COLOR = QColor(30, 30, 30)

class HarnessScene(QGraphicsScene):
    """The infinite drawing board."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(BG_COLOR))
        # Set a massive scene rect so it feels infinite
        self.setSceneRect(-50000, -50000, 100000, 100000)

    def drawBackground(self, painter, rect):
        """High-performance grid rendering."""
        super().drawBackground(painter, rect)
        
        # 1. Calculate grid lines visible in the current 'rect'
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        # Align to grid snap
        first_left = left - (left % GRID_SIZE)
        first_top = top - (top % GRID_SIZE)

        # 2. Draw lines
        lines = []
        
        # Vertical lines
        x = first_left
        while x <= right:
            lines.append(QLineF(x, top, x, bottom))
            x += GRID_SIZE
            
        # Horizontal lines
        y = first_top
        while y <= bottom:
            lines.append(QLineF(left, y, right, y))
            y += GRID_SIZE

        # 3. Render
        painter.setPen(QPen(GRID_COLOR, 1))
        painter.drawLines(lines)

class HarnessView(QGraphicsView):
    """The Window looking into the Scene."""
    def __init__(self, scene=None):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag) # Middle-click pan
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        """Zoom Logic."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)
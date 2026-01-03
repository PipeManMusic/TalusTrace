from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF
from talustrace.backend.models import Side

# Visual Constants
BOX_COLOR = QColor(50, 50, 50)
BORDER_COLOR = QColor(200, 200, 200)
TEXT_COLOR = QColor(255, 255, 255)
PIN_COLOR = QColor(200, 200, 200)
PIN_PITCH = 15  # Distance between pins

class DeviceItem(QGraphicsRectItem):
    """Visual representation of a Device (Box + Pins on 4 Sides)."""
    def __init__(self, device_model):
        super().__init__()
        self.model = device_model
        
        # 1. Setup Appearance
        self.setBrush(QBrush(BOX_COLOR))
        self.setPen(QPen(BORDER_COLOR, 2))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        # 2. Add Label
        self.label = QGraphicsSimpleTextItem(self.model.label, self)
        self.label.setBrush(QBrush(TEXT_COLOR))
        self.label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # 3. Sort Pins by Side
        pins = self.model.pins if isinstance(self.model.pins, list) else []
        p_left = [p for p in pins if p.side == Side.LEFT]
        p_right = [p for p in pins if p.side == Side.RIGHT]
        p_top = [p for p in pins if p.side == Side.TOP]
        p_bottom = [p for p in pins if p.side == Side.BOTTOM]
        
        # 4. Calculate Dimensions
        # Height is driven by Left/Right pins
        lr_max = max(len(p_left), len(p_right))
        # Width is driven by Top/Bottom pins OR the label width
        tb_max = max(len(p_top), len(p_bottom))
        
        # Base dimensions
        label_w = self.label.boundingRect().width()
        label_h = self.label.boundingRect().height()
        
        # Calculate Box Size
        # Width = Max of (Label width, Top/Bottom pins * pitch)
        width = max(label_w + 30, (tb_max * PIN_PITCH) + 20)
        
        # Height = Max of (Label height, Left/Right pins * pitch)
        height = max(label_h + 20, (lr_max * PIN_PITCH) + 20)
        
        # If we have top pins, add padding to push label down
        top_padding = 10 if not p_top else 20
        height += top_padding

        self.setRect(0, 0, width, height)
        
        # 5. Position Label (Centered)
        lb = self.label.boundingRect()
        self.label.setPos((width - lb.width()) / 2, (height - lb.height()) / 2)

        # 6. Draw Pins
        
        # LEFT PINS (Top to Bottom)
        for i, _ in enumerate(p_left):
            y = top_padding + (i * PIN_PITCH) + (PIN_PITCH/2)
            self._draw_pin_line(-5, y, 0, y)

        # RIGHT PINS (Top to Bottom)
        for i, _ in enumerate(p_right):
            y = top_padding + (i * PIN_PITCH) + (PIN_PITCH/2)
            self._draw_pin_line(width, y, width + 5, y)

        # TOP PINS (Left to Right)
        # Center the group of pins relative to the box width
        t_start_x = (width - (len(p_top) * PIN_PITCH)) / 2
        for i, _ in enumerate(p_top):
            x = t_start_x + (i * PIN_PITCH) + (PIN_PITCH/2)
            self._draw_pin_line(x, -5, x, 0)

        # BOTTOM PINS (Left to Right)
        b_start_x = (width - (len(p_bottom) * PIN_PITCH)) / 2
        for i, _ in enumerate(p_bottom):
            x = b_start_x + (i * PIN_PITCH) + (PIN_PITCH/2)
            self._draw_pin_line(x, height, x, height + 5)

        # 7. Sync Position
        self.setPos(self.model.x, self.model.y)

    def _draw_pin_line(self, x1, y1, x2, y2):
        line = QGraphicsLineItem(x1, y1, x2, y2, self)
        line.setPen(QPen(PIN_COLOR, 2))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.model.x = self.pos().x()
        self.model.y = self.pos().y()
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF
from talustrace.backend.models import Side

# Visual Constants
GRID_SIZE = 20  # MUST Match the Canvas Grid
BOX_COLOR = QColor(50, 50, 50)
BORDER_COLOR = QColor(200, 200, 200)
TEXT_COLOR = QColor(255, 255, 255)
PIN_COLOR = QColor(200, 200, 200)
PIN_PITCH = 20 # Sync Pin Pitch with Grid Size for perfect alignment!

class DeviceItem(QGraphicsRectItem):
    """Visual representation of a Device with Grid Snapping."""
    def __init__(self, device_model):
        super().__init__()
        self.model = device_model
        
        self.attached_wires = [] 
        self.pin_positions = {} 

        # 1. Setup Appearance
        self.setBrush(QBrush(BOX_COLOR))
        self.setPen(QPen(BORDER_COLOR, 2))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        
        # 2. Add Label
        self.label = QGraphicsSimpleTextItem(self.model.label, self)
        self.label.setBrush(QBrush(TEXT_COLOR))
        self.label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # 3. Sort Pins
        pins = self.model.pins if isinstance(self.model.pins, list) else []
        p_left = [p for p in pins if p.side == Side.LEFT]
        p_right = [p for p in pins if p.side == Side.RIGHT]
        p_top = [p for p in pins if p.side == Side.TOP]
        p_bottom = [p for p in pins if p.side == Side.BOTTOM]
        
        # 4. Calculate Dimensions (Snapped to Grid)
        lr_max = max(len(p_left), len(p_right))
        tb_max = max(len(p_top), len(p_bottom))
        
        # Calculate raw sizes
        raw_w = max(self.label.boundingRect().width() + 40, (tb_max * PIN_PITCH) + 20)
        raw_h = max(30, (lr_max * PIN_PITCH) + 20)
        
        # Add Top Padding
        top_padding = PIN_PITCH if p_top else 10
        raw_h += top_padding

        # SNAP DIMENSIONS TO GRID
        # We round UP to the nearest grid size to ensure pins land on lines
        width = (int(raw_w / GRID_SIZE) + 1) * GRID_SIZE
        height = (int(raw_h / GRID_SIZE) + 1) * GRID_SIZE

        self.setRect(0, 0, width, height)
        
        # Position Label
        lb = self.label.boundingRect()
        self.label.setPos((width - lb.width()) / 2, (height - lb.height()) / 2)

        # 5. Draw Pins (Aligned to Grid)
        
        # LEFT PINS
        # Start at first grid intersection below top
        start_y = (int(top_padding / GRID_SIZE) + 1) * GRID_SIZE
        for i, pin in enumerate(p_left):
            y = start_y + (i * PIN_PITCH)
            self._draw_pin_line(-5, y, 0, y)
            self.pin_positions[pin.id] = QPointF(-5, y)

        # RIGHT PINS
        start_y = (int(top_padding / GRID_SIZE) + 1) * GRID_SIZE
        for i, pin in enumerate(p_right):
            y = start_y + (i * PIN_PITCH)
            self._draw_pin_line(width, y, width + 5, y)
            self.pin_positions[pin.id] = QPointF(width + 5, y)

        # TOP PINS
        # Center them on grid lines
        # This is trickier, simplified to start from left for now
        start_x = GRID_SIZE 
        for i, pin in enumerate(p_top):
            x = start_x + (i * PIN_PITCH)
            self._draw_pin_line(x, -5, x, 0)
            self.pin_positions[pin.id] = QPointF(x, -5)

        # BOTTOM PINS
        start_x = GRID_SIZE
        for i, pin in enumerate(p_bottom):
            x = start_x + (i * PIN_PITCH)
            self._draw_pin_line(x, height, x, height + 5)
            self.pin_positions[pin.id] = QPointF(x, height + 5)

        # 6. Initial Snap
        self.setPos(self._snap(self.model.x), self._snap(self.model.y))

    def _draw_pin_line(self, x1, y1, x2, y2):
        line = QGraphicsLineItem(x1, y1, x2, y2, self)
        line.setPen(QPen(PIN_COLOR, 2))

    def _snap(self, value):
        """Rounds value to nearest GRID_SIZE."""
        return round(value / GRID_SIZE) * GRID_SIZE

    def itemChange(self, change, value):
        """Intercept movement and force Snap-to-Grid."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            new_pos.setX(self._snap(new_pos.x()))
            new_pos.setY(self._snap(new_pos.y()))
            return new_pos

        if change == QGraphicsItem.ItemPositionHasChanged:
            self.model.x = self.pos().x()
            self.model.y = self.pos().y()
            for wire in self.attached_wires:
                wire.update_geometry()
                
        return super().itemChange(change, value)

class WireItem(QGraphicsLineItem):
    """Visual representation of a Wire with Live Tracking."""
    def __init__(self, wire_model, source_item=None, target_item=None):
        super().__init__()
        self.model = wire_model
        
        self.source_item = source_item
        self.target_item = target_item
        
        self.src_pin_id = self.model.from_conn.split('.')[1]
        self.tgt_pin_id = self.model.to_conn.split('.')[1]

        if self.source_item:
            self.source_item.attached_wires.append(self)
        if self.target_item:
            self.target_item.attached_wires.append(self)

        color_map = {
            "RD": QColor(255, 0, 0), "BK": QColor(0, 0, 0), 
            "WH": QColor(255, 255, 255), "PK": QColor(255, 192, 203),
            "GN": QColor(0, 255, 0), "BL": QColor(0, 0, 255)
        }
        c = color_map.get(self.model.color, QColor(150, 150, 150))
        pen = QPen(c, 3)
        pen.setCapStyle(Qt.RoundCap)
        if self.model.stripe:
            pen.setStyle(Qt.DashLine)
        
        self.setPen(pen)
        self.setZValue(-1)
        
        self.update_geometry()

    def update_geometry(self):
        if not self.source_item or not self.target_item:
            return

        src_offset = self.source_item.pin_positions.get(self.src_pin_id, QPointF(0,0))
        p1 = self.source_item.pos() + src_offset
        
        tgt_offset = self.target_item.pin_positions.get(self.tgt_pin_id, QPointF(0,0))
        p2 = self.target_item.pos() + tgt_offset
        
        self.setLine(QLineF(p1, p2))
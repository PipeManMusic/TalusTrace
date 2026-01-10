from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
        super().__init__(-1.0, -1.0, 2.0, 2.0, parent)
        self.pin = pin_model
        self.setBrush(QBrush(QColor(THEME_FALLBACK["pin_fill"])))
        self.setPen(Qt.NoPen)
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.cyan)) 
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(THEME_FALLBACK["pin_fill"])))
        super().hoverLeaveEvent(event)

class DeviceItem(SelectableItemMixin, QGraphicsRectItem):
    def __init__(self, device, is_ghost=False, parent=None):
        QGraphicsRectItem.__init__(self, parent)
        
        width_mm = device.meta.get("width_mm", 40.0)
        height_mm = device.meta.get("height_mm", 30.0)
        self.setRect(-width_mm/2, -height_mm/2, width_mm, height_mm)
        self.setPos(device.x, device.y)
        
        rotation = getattr(device, 'rotation', 0.0)
        self.setRotation(rotation)
        
        self.init_mixin(device, is_ghost)
        
        if not self.is_ghost and hasattr(device, 'pins'):
            for pin in device.pins:
                pin_item = PinItem(pin, self)
                pin_item.setPos(pin.x, pin.y)

    # FIX: Restore backward compatibility for tests accessing .device
    @property
    def device(self):
        return self.model

    @device.setter
    def device(self, value):
        self.model = value

    def boundingRect(self):
        return super().boundingRect().adjusted(-25, -25, 25, 25)

    def _apply_style(self):
        body_color = QColor(THEME_FALLBACK["device_body"])
        outline_color = QColor(THEME_FALLBACK["device_outline"])

        if self.is_ghost:
            body_color.setAlpha(100)
            self.setPen(QPen(outline_color, 1, Qt.DashLine))
        else:
            self.setPen(QPen(outline_color, 0))
            
        self.setBrush(QBrush(body_color))

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() and not self.is_ghost:
            rect = self.rect().adjusted(-4, -4, 4, 4)
            painter.setPen(QPen(QColor(0, 180, 255, 100), 4, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

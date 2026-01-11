from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin
from api.manager import APIManager
from ui.items.pin import PinItem # <--- FIXED IMPORT

class DeviceItem(SelectableItemMixin, QGraphicsRectItem):
    def __init__(self, device, is_ghost=False, parent=None):
        QGraphicsRectItem.__init__(self, parent)
        
        transformer = APIManager.get_instance().transformer
        
        width_mm = device.meta.get("width_mm", 40.0)
        height_mm = device.meta.get("height_mm", 30.0)
        
        width_px = transformer.mm_to_px(width_mm)
        height_px = transformer.mm_to_px(height_mm)
        
        self.setRect(0, 0, width_px, height_px)
        self.setTransformOriginPoint(width_px / 2, height_px / 2)
        
        px = transformer.mm_to_px(device.x)
        py = transformer.mm_to_px(device.y)
        self.setPos(px, py)
        
        rotation = getattr(device, 'rotation', 0.0)
        self.setRotation(rotation)
        
        self.init_mixin(device, is_ghost)
        
        if not self.is_ghost and hasattr(device, 'pins'):
            for pin in device.pins:
                pin_item = PinItem(pin, self)
                pin_px = transformer.mm_to_px(pin.x)
                pin_py = transformer.mm_to_px(pin.y)
                pin_item.setPos(pin_px, pin_py)

    @property
    def device(self):
        return self.model

    @device.setter
    def device(self, value):
        self.model = value

    def boundingRect(self):
        return super().boundingRect().adjusted(-5, -5, 5, 5)

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
            rect = self.rect().adjusted(-2, -2, 2, 2)
            painter.setPen(QPen(QColor(0, 180, 255, 100), 2, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
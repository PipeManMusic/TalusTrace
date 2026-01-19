from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from ui.items.pin import PinItem

class DeviceItem(ObservableGraphicsItemMixin, SelectableItemMixin, QGraphicsRectItem):
    __test_scenario__ = {
        'model_data': {'meta': {'width_mm': 40.0, 'height_mm': 30.0}, 'x': 0, 'y': 0, 'rotation': 0.0, 'pins': []},
        'expected_child_count': 0
    }
    def __init__(self, device, is_ghost=False, parent=None):
        QGraphicsRectItem.__init__(self, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self.setZValue(10)  # Devices above wires

        # ARCHITECTURE UPDATE: Use MM dimensions directly
        width_mm = device.meta.get("width_mm", 40.0)
        height_mm = device.meta.get("height_mm", 30.0)

        self.setRect(0, 0, width_mm, height_mm)
        self.setTransformOriginPoint(width_mm / 2, height_mm / 2)

        # No conversion needed. Model x/y is MM. Scene is MM.
        self.setPos(device.x, device.y)

        rotation = getattr(device, 'rotation', 0.0)
        self.setRotation(rotation)

        self.init_mixin(device, is_ghost)

        if not self.is_ghost and hasattr(device, 'pins'):
            for pin in device.pins:
                pin_item = PinItem(pin, self)
                # Pin positions in model are relative MM. Use directly.
                pin_item.setPos(pin.x, pin.y)

        # Subscribe to model_changed events for this device
        from api.manager import APIManager
        self._api = APIManager.get_instance()
        self._api.subscribe(self._on_model_changed)

        # Debug output for hit test diagnosis
        print(f'[DeviceItem] Created: id={getattr(device, "id", None)}, scenePos={self.scenePos()}, pos={self.pos()}, rect={self.rect()}, boundingRect={self.boundingRect()}')

    def _on_model_changed(self, data):
        # Only update if this device moved
        if not data or 'item' not in data:
            return
        item = data['item']
        if hasattr(item, 'id') and hasattr(self.model, 'id') and item.id == self.model.id:
            # Update position to match model
            self.setPos(self.model.x, self.model.y)

    @property
    def device(self):
        return self.model

    @device.setter
    def device(self, value):
        self.model = value

    def boundingRect(self):
        # Adjust slightly for selection halo
        return super().boundingRect().adjusted(-2, -2, 2, 2)

    def _apply_style(self):
        body_color = QColor(THEME_FALLBACK["device_body"])
        outline_color = QColor(THEME_FALLBACK["device_outline"])
        
        # Cosmetic Pen (Width 0) ensures it draws nicely at any zoom level
        pen_style = Qt.DashLine if self.is_ghost else Qt.SolidLine
        pen = QPen(outline_color, 0, pen_style)
        pen.setCosmetic(True)

        if self.is_ghost:
            body_color.setAlpha(100)

        self.setPen(pen)
        self.setBrush(QBrush(body_color))

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() and not self.is_ghost:
            rect = self.rect().adjusted(-1, -1, 1, 1)
            pen = QPen(QColor(0, 180, 255, 150), 0, Qt.SolidLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
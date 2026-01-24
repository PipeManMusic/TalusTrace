"""
DeviceItem: QGraphicsRectItem subclass for representing devices in the scene.
Handles device geometry, style, and pin placement.
"""
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from ui.items.pin import PinItem

class DeviceItem(ObservableGraphicsItemMixin, SelectableItemMixin, QGraphicsRectItem):
    """
    QGraphicsRectItem subclass for device visualization and interaction.
    Handles device geometry, style, and pin placement in the scene.
    """
    __test_scenario__ = {
        'model_data': {'meta': {'width_mm': 40.0, 'height_mm': 30.0}, 'x': 0, 'y': 0, 'rotation': 0.0, 'pins': []},
        'expected_child_count': 0
    }
    def __init__(self, device, is_ghost=False, parent=None):
        """
        Initialize the DeviceItem.
        Args:
            device: The device model object.
            is_ghost (bool): Whether this is a ghost (preview) item.
            parent: Optional parent QGraphicsItem.
        """
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




    def update_from_model(self):
        """
        Update the item's position and visuals to match the model.
        """
        # Always update position and visuals to match model
        self.setPos(self.model.x, self.model.y)
        self.update()  # Force redraw in case of visual artifacts

    @property
    def device(self):
        """
        Get the device model associated with this item.
        Returns:
            The device model object.
        """
        return self.model

    @device.setter
    def device(self, value):
        """
        Set the device model for this item.
        Args:
            value: The new device model object.
        """
        self.model = value

    def boundingRect(self):
        """
        Return the bounding rectangle, adjusted for selection halo.
        Returns:
            QRectF: The adjusted bounding rectangle.
        """
        return super().boundingRect().adjusted(-2, -2, 2, 2)

    def _apply_style(self):
        """
        Apply the visual style (pen and brush) to the device item.
        """
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
        """
        Paint the device item, including selection highlight if selected.
        Args:
            painter: QPainter object.
            option: QStyleOptionGraphicsItem.
            widget: Optional widget being painted on.
        """
        super().paint(painter, option, widget)
        if self.isSelected() and not self.is_ghost:
            rect = self.rect().adjusted(-1, -1, 1, 1)
            pen = QPen(QColor(0, 180, 255, 150), 0, Qt.SolidLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
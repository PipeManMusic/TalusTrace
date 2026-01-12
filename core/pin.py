from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt
from ui.theme import ThemeManager

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
        # 1. Geometry Setup (World Space / Millimeters)
        # We draw a circle with diameter 1.0mm, centered at (0,0) locally.
        # This allows the canvas to place it at the correct X,Y simply by setting position.
        super().__init__(-0.5, -0.5, 1.0, 1.0, parent)
        
        self.pin = pin_model
        self.theme = ThemeManager()
        
        # 2. Visual Style
        color = self.theme.get_color("pin_fill")
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        
        # 3. Interaction Setup
        self.setAcceptHoverEvents(True)
        
        # CRITICAL: This flag allows the SelectTool to "pick" this item.
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Optional: Set True if you want clicks to stop propagating to the Device.
        # Currently False, so if you miss the pin hit-box, you select the Device.
        # self.setFlag(QGraphicsItem.ItemStopsClickFocusPropagation, True)

    @property
    def model(self):
        """
        Public Interface for Tools.
        The SelectTool accesses 'item.model' to populate the Property Panel.
        """
        return self.pin

    def hoverEnterEvent(self, event):
        # Visual feedback on hover (Cyan)
        self.setBrush(QBrush(Qt.cyan))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Return to normal or selected color
        if self.isSelected():
            self.setBrush(QBrush(Qt.green))
        else:
            color = self.theme.get_color("pin_fill")
            self.setBrush(QBrush(color))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        # Sync Selection State with Visuals
        if change == QGraphicsItem.ItemSelectedChange:
            if value: 
                # Selected Color
                self.setBrush(QBrush(Qt.green))
            else:
                # Default Color
                color = self.theme.get_color("pin_fill")
                self.setBrush(QBrush(color))
        return super().itemChange(change, value)

    def shape(self):
        """
        Hit-Box Definition.
        We return a larger area (3mm diameter) than the visual circle (1mm)
        to make the pin easier to click with the mouse.
        """
        path = QPainterPath()
        path.addEllipse(-1.5, -1.5, 3.0, 3.0)
        return path
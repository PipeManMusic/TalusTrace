from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QTransform
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

# --- THEME CONSTANTS ---
THEME_GREY = QColor("#D0D0D0")
GRID_SIZE = 20

class ElbowHandle(QGraphicsItem):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.radius = 2.5
        self.setZValue(2)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, 2*r, 2*r)

    def paint(self, painter, option, widget=None):
        brush = QBrush(THEME_GREY)
        if option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            parent = self.parentItem()
            if parent:
                scene_pos = parent.mapToScene(new_pos)
                sx = round(scene_pos.x() / GRID_SIZE) * GRID_SIZE
                sy = round(scene_pos.y() / GRID_SIZE) * GRID_SIZE
                return parent.mapFromScene(QPointF(sx, sy))

        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                elbows = parent.model.elbows
                if 0 <= self.index < len(elbows):
                    elbows[self.index] = (self.pos().x(), self.pos().y())
                    parent.update_layout()
                    
        return super().itemChange(change, value)

class TwistAnchorItem(QGraphicsItem):
    def __init__(self, pos, parent=None, side=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        
        self.radius = 2.5
        self.side = side 
        self.pins = []
        self.leaders = []
        
        for i in range(2):
            pin = QGraphicsEllipseItem(-3, -3, 6, 6, self)
            pin.setBrush(QBrush(THEME_GREY))
            pin.setPen(Qt.NoPen)
            self.pins.append(pin)
            
            leader = QGraphicsLineItem(self)
            leader.setPen(QPen(THEME_GREY, 3, Qt.SolidLine))
            leader.setZValue(1)
            leader.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            self.leaders.append(leader)
            
        self.setPos(*pos)

    def rotate_90(self):
        parent = self.parentItem()
        if not parent or not hasattr(parent, "model"):
            return
        model = parent.model
        if self.side == 'a':
            model.rotation_a = (getattr(model, 'rotation_a', 0) + 90) % 360
        elif self.side == 'b':
            model.rotation_b = (getattr(model, 'rotation_b', 0) + 90) % 360
        if hasattr(parent, "update_layout"):
            parent.update_layout()

    def paint(self, painter, option, widget=None):
        brush = QBrush(THEME_GREY)
        if option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius))

    def boundingRect(self):
        r = self.radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, "update_layout"):
                parent.update_layout()
        return super().itemChange(change, value)

class DoubleHelixPathItem(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path1 = QPainterPath()
        self.path2 = QPainterPath()
        self.color1 = THEME_GREY
        self.color2 = THEME_GREY
        self._rect = QRectF(0, 0, 1, 1)

    def set_strand_colors(self, color1: QColor, color2: QColor):
        self.color1 = color1
        self.color2 = color2
        self.update()

    def update_geometry(self, start: QPointF, end: QPointF, elbows=None):
        self.prepareGeometryChange()
        points = [start] + (elbows or []) + [end]
        self.path1 = QPainterPath()
        self.path2 = QPainterPath()
        
        for i in range(len(points) - 1):
            s = (points[i].x(), points[i].y())
            e = (points[i+1].x(), points[i+1].y())
            strand1, strand2 = calculate_double_helix(s, e, 5.0, 20.0)
            
            if strand1:
                if i == 0: self.path1.moveTo(QPointF(*strand1[0]))
                else: self.path1.lineTo(QPointF(*strand1[0]))
                for pt in strand1: self.path1.lineTo(QPointF(*pt))
            if strand2:
                if i == 0: self.path2.moveTo(QPointF(*strand2[0]))
                else: self.path2.lineTo(QPointF(*strand2[0]))
                for pt in strand2: self.path2.lineTo(QPointF(*pt))
                    
        self._rect = self.path1.boundingRect().united(self.path2.boundingRect())

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color1, 3))
        painter.drawPath(self.path1)
        painter.setPen(QPen(self.color2, 3))
        painter.drawPath(self.path2)

class TwistedPairItem(QGraphicsObject):
    def __init__(self, model: TwistedPair, parent=None, on_changed=None): # Fixed TypeError
        super().__init__(parent)
        self.model = model
        self.on_changed = on_changed
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Local visual state for colors
        self._wire_colors = [THEME_GREY, THEME_GREY]
        
        self.helix = DoubleHelixPathItem(self)
        self.elbow_handles = []
        
        # Anchors
        self.anchor_a = TwistAnchorItem(model.node_a, self, side='a')
        self.anchor_b = TwistAnchorItem(model.node_b, self, side='b')
        
        self.update_layout()

    def set_signal(self, pin_item, wire_id, color): # Fixed Integration Test Failures
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            return

        if idx == 0:
            self.model.wire_id_1 = wire_id
            self._wire_colors[0] = QColor(color)
        else:
            self.model.wire_id_2 = wire_id
            self._wire_colors[1] = QColor(color)
        
        self.update_layout()

    def update_layout(self):
        # Initialization Guard
        if not hasattr(self, 'anchor_a') or not hasattr(self, 'anchor_b'):
            return

        def snap(pt):
            return QPointF(round(pt.x() / GRID_SIZE) * GRID_SIZE, round(pt.y() / GRID_SIZE) * GRID_SIZE)

        self.helix.set_strand_colors(self._wire_colors[0], self._wire_colors[1])

        for anchor, side_rot_attr in [(self.anchor_a, 'rotation_a'), (self.anchor_b, 'rotation_b')]:
            anchor.setPos(self.mapFromScene(snap(anchor.scenePos())))
            rot = getattr(self.model, side_rot_attr, 0)
            t = QTransform().rotate(rot)
            offsets = [t.map(QPointF(-20, 20)), t.map(QPointF(-20, -20))]
            for i, (pin, leader) in enumerate(zip(anchor.pins, anchor.leaders)):
                color = self._wire_colors[i]
                pin.setBrush(QBrush(color))
                leader.setPen(QPen(color, 3))
                pin.setPos(offsets[i])
                leader.setLine(0, 0, offsets[i].x(), offsets[i].y())

        elbows_data = getattr(self.model, 'elbows', [])
        while len(self.elbow_handles) < len(elbows_data):
            self.elbow_handles.append(ElbowHandle(len(self.elbow_handles), self))
        while len(self.elbow_handles) > len(elbows_data):
            h = self.elbow_handles.pop()
            if h.scene(): h.scene().removeItem(h)

        for i, h in enumerate(self.elbow_handles):
            h.index = i
            if not (h.isSelected() or h.isUnderMouse()):
                h.setPos(QPointF(*elbows_data[i]))

        self.helix.update_geometry(self.anchor_a.pos(), self.anchor_b.pos(), [QPointF(*e) for e in elbows_data])
        
        if self.on_changed:
            self.on_changed()

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass
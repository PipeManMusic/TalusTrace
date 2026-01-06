from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QTransform
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

# --- THEME COLORS ---
THEME_GREY = QColor("#D0D0D0")

class ElbowHandle(QGraphicsItem):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # CRITICAL: This flag enables itemChange notifications during drag
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.radius = 2.5
        self.setZValue(2)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, 2*r, 2*r)

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(THEME_GREY)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        # Snap to Scene Grid (20px) during movement
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value  # This is in Local Coordinates
            parent = self.parentItem()
            
            if parent:
                # Map to Scene to check grid alignment (Robust to parent moves/rotations)
                scene_pos = parent.mapToScene(new_pos)
                sx = round(scene_pos.x() / 20.0) * 20.0
                sy = round(scene_pos.y() / 20.0) * 20.0
                
                # Map snapped scene point back to local
                return parent.mapFromScene(QPointF(sx, sy))
            else:
                # Fallback if no parent (shouldn't happen for handles)
                x = round(new_pos.x() / 20.0) * 20.0
                y = round(new_pos.y() / 20.0) * 20.0
                return QPointF(x, y)

        # Update model after movement is committed
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                elbows = parent.model.elbows
                if 0 <= self.index < len(elbows):
                    # Update model with new position
                    elbows[self.index] = (self.pos().x(), self.pos().y())
                    # Trigger redraw of the wire
                    parent.update_layout()
                    
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                if 0 <= self.index < len(parent.model.elbows):
                    del parent.model.elbows[self.index]
                    parent.update_layout()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()


class TwistAnchorItem(QGraphicsItem):
    def __init__(self, pos, parent=None, side=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        
        # Default size matching theme (5px diameter)
        self.radius = 2.5
        self.setPos(*pos)
        self.side = side  # 'a' or 'b'
        
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
            # Ensure leaders draw behind the anchor grip
            leader.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            self.leaders.append(leader)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rotate_90()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

    def hoverEnterEvent(self, event):
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.update()
        super().hoverLeaveEvent(event)

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

    def boundingRect(self):
        r = self.radius
        # Inflate bounding rect slightly to avoid rendering artifacts
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(THEME_GREY)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius))

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
        self.color1 = QColor(Qt.red)
        self.color2 = QColor(Qt.blue)
        self._rect = QRectF(0, 0, 1, 1)

    def set_strand_colors(self, color1: QColor, color2: QColor):
        self.color1 = color1
        self.color2 = color2
        self.update()

    def update_geometry(self, start: QPointF, end: QPointF, elbows=None):
        if elbows is None:
            elbows = []
        self.prepareGeometryChange()
        amp = 5.0
        wavelength = 20.0
        points = [start] + elbows + [end]
        self.path1 = QPainterPath()
        self.path2 = QPainterPath()
        
        for i in range(len(points) - 1):
            p_start = points[i]
            p_end = points[i+1]
            s = (p_start.x(), p_start.y())
            e = (p_end.x(), p_end.y())
            strand1, strand2 = calculate_double_helix(s, e, amp, wavelength)
            
            if strand1:
                if i == 0:
                    self.path1.moveTo(QPointF(*strand1[0]))
                else:
                    self.path1.lineTo(QPointF(*strand1[0]))
                for pt in strand1[1:]:
                    self.path1.lineTo(QPointF(*pt))
            
            if strand2:
                if i == 0:
                    self.path2.moveTo(QPointF(*strand2[0]))
                else:
                    self.path2.lineTo(QPointF(*strand2[0]))
                for pt in strand2[1:]:
                    self.path2.lineTo(QPointF(*pt))
                    
        self._rect = self.path1.boundingRect().united(self.path2.boundingRect())

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color1, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path1)
        painter.setPen(QPen(self.color2, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path2)


class TwistedPairItem(QGraphicsObject):
    def __init__(self, model: TwistedPair, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.anchor_a = TwistAnchorItem(model.node_a, self, side='a')
        self.anchor_b = TwistAnchorItem(model.node_b, self, side='b')
        self.helix = DoubleHelixPathItem(self)
        self.elbow_handles = []
        self.update_layout()

    def update_layout(self):
        if not hasattr(self, "anchor_a") or not hasattr(self, "anchor_b"):
            return

        def snap_point(pt):
            return QPointF(round(pt.x() / 20) * 20, round(pt.y() / 20) * 20)

        def rotated_offsets(rotation):
            base = [QPointF(-20, 20), QPointF(-20, -20)]
            t = QTransform()
            t.rotate(rotation)
            return [t.map(offset) for offset in base]

        def points_close(p1, p2, eps=0.01):
            return (abs(p1.x() - p2.x()) < eps) and (abs(p1.y() - p2.y()) < eps)

        def color_for_wire(wire_id, default):
            if wire_id is None:
                return default
            if wire_id == 1:
                return QColor("blue")
            if wire_id == 2:
                return QColor("red")
            return default

        color1 = color_for_wire(getattr(self.model, 'wire_id_1', None), THEME_GREY)
        color2 = color_for_wire(getattr(self.model, 'wire_id_2', None), THEME_GREY)

        # Update Anchors
        for anchor, side_rot_attr in [(self.anchor_a, 'rotation_a'), (self.anchor_b, 'rotation_b')]:
            pos_scene = anchor.scenePos()
            snap_scene = snap_point(pos_scene)
            if not points_close(pos_scene, snap_scene):
                snap_local = self.mapFromScene(snap_scene)
                anchor.setPos(snap_local)
            
            rot = getattr(self.model, side_rot_attr, 0) % 360
            offsets = rotated_offsets(rot)
            
            for i, (pin, leader) in enumerate(zip(anchor.pins, anchor.leaders)):
                c = color1 if i == 0 else color2
                pin.setBrush(QBrush(c))
                leader.setPen(QPen(c, 3, Qt.SolidLine))
                pin.setPos(offsets[i])
                leader.setLine(0, 0, offsets[i].x(), offsets[i].y())

        # Sync Elbow Handles
        elbows_data = getattr(self.model, 'elbows', [])
        while len(self.elbow_handles) < len(elbows_data):
            handle = ElbowHandle(len(self.elbow_handles), self)
            self.elbow_handles.append(handle)
        while len(self.elbow_handles) > len(elbows_data):
            handle = self.elbow_handles.pop()
            handle.setParentItem(None)
            if handle.scene():
                handle.scene().removeItem(handle)

        for i, handle in enumerate(self.elbow_handles):
            handle.index = i
            pos = elbows_data[i]
            # Only update handle position if it's not the one currently driving the drag
            if not (handle.isSelected() or handle.isUnderMouse()):
                handle.setPos(QPointF(pos[0], pos[1]))

        # Update Helix
        self.helix.set_strand_colors(color1, color2)
        elbow_points = [QPointF(e[0], e[1]) for e in elbows_data]
        self.helix.update_geometry(self.anchor_a.pos(), self.anchor_b.pos(), elbow_points)

    def mouseDoubleClickEvent(self, event):
        scene_pos = event.scenePosition().toPointF() if hasattr(event, 'scenePosition') else event.scenePos()
        pos = self.mapFromScene(scene_pos)
        
        points = [self.anchor_a.pos()] + [QPointF(e[0], e[1]) for e in self.model.elbows] + [self.anchor_b.pos()]
        min_dist = float('inf')
        insert_idx = 0
        
        for i in range(len(points) - 1):
            a, b = points[i], points[i+1]
            ab = b - a
            ab_len2 = ab.x()**2 + ab.y()**2
            if ab_len2 == 0:
                t = 0
            else:
                t = max(0, min(1, ((pos - a).x()*ab.x() + (pos - a).y()*ab.y()) / ab_len2))
            proj = a + ab * t
            dist = (proj - pos).manhattanLength()
            if dist < min_dist:
                min_dist = dist
                insert_idx = i
        
        self.model.elbows.insert(insert_idx, (pos.x(), pos.y()))
        self.update_layout()
        event.accept()

    def set_signal(self, pin_item, wire_id, color):
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            raise ValueError("Pin not found in anchors")

        if idx == 0:
            self.model.wire_id_1 = wire_id
        elif idx == 1:
            self.model.wire_id_2 = wire_id

        self.update_layout()

    def get_signal(self, pin_item):
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            raise ValueError("Pin not found in anchors")
        if idx == 0:
            return self.model.wire_id_1
        elif idx == 1:
            return self.model.wire_id_2
        return None

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QTransform
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

# --- THEME COLORS ---
THEME_GREY = QColor("#D0D0D0")

# --- ELBOW HANDLE ---
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
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(THEME_GREY)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        # Snap to grid (20px) during movement
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            x = round(new_pos.x() / 20.0) * 20.0
            y = round(new_pos.y() / 20.0) * 20.0
            return QPointF(x, y)

        # Update model after movement is committed
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                elbows = parent.model.elbows
                if 0 <= self.index < len(elbows):
                    elbows[self.index] = (self.pos().x(), self.pos().y())
                    parent.update_layout()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                if 0 <= self.index < len(parent.model.elbows):
                    del parent.model.elbows[self.index]
                    parent.update_layout()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

class TwistAnchorItem(QGraphicsItem):
    def __init__(self, pos, parent=None, side=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        # Try to load grip_size_px from theme, default to 5, radius is half
        try:
            import json
            with open("docs/theme_tokens.json") as f:
                theme = json.load(f)
            self.radius = float(theme.get("grip_size_px", 5)) / 2
        except Exception:
            self.radius = 2.5
        self.setPos(*pos)
        self.side = side  # 'a' or 'b'
        # Create two pins and two leaders as children of the anchor
        self.pins = []
        self.leaders = []
        # Theme color for default wire (grey_300)
        theme_grey = QColor("#D0D0D0")
        for i in range(2):
            pin = QGraphicsEllipseItem(-3, -3, 6, 6, self)  # 6px diameter circle
            pin.setBrush(QBrush(theme_grey))
            pin.setPen(Qt.NoPen)
            self.pins.append(pin)
            leader = QGraphicsLineItem(self)
            leader.setPen(QPen(theme_grey, 3, Qt.SolidLine))
            leader.setZValue(1)
            leader.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            self.leaders.append(leader)

    def hoverEnterEvent(self, event):
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.update()
        super().hoverLeaveEvent(event)

    def rotate_90(self):
        """
        Increment this anchor's rotation by 90 degrees (modulo 360),
        update the corresponding model field (rotation_a or rotation_b),
        and trigger a layout refresh on the parent TwistedPairItem.
        """
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

    def boundingRect(self):
        r = self.radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None):
        # Interaction palette: Drag > Selected > Hover > Default
        theme_grey = QColor("#D0D0D0")
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(theme_grey)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

    def itemChange(self, change, value):
        # Only trigger layout update after the position has actually changed
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, "update_layout"):
                parent.update_layout()
        return super().itemChange(change, value)
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsSceneMouseEvent, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QTransform
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

# --- THEME COLORS ---
THEME_GREY = QColor("#D0D0D0")

# --- ELBOW HANDLE ---
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
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(THEME_GREY)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                elbows = parent.model.elbows
                if 0 <= self.index < len(elbows):
                    elbows[self.index] = (self.pos().x(), self.pos().y())
                    parent.update_layout()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                if 0 <= self.index < len(parent.model.elbows):
                    del parent.model.elbows[self.index]
                    parent.update_layout()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsSceneMouseEvent, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

class ElbowHandle(QGraphicsItem):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(3)
        self.radius = 4
        self.setCursor(Qt.OpenHandCursor)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, 2*r, 2*r)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor('cyan')))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                elbows = parent.model.elbows
                if 0 <= self.index < len(elbows):
                    elbows[self.index] = (self.pos().x(), self.pos().y())
                    parent.update_layout()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                if 0 <= self.index < len(parent.model.elbows):
                    del parent.model.elbows[self.index]
                    parent.update_layout()
            event.accept()
        else:
            super().mousePressEvent(event)
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsSceneMouseEvent, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

class TwistAnchorItem(QGraphicsItem):
    def mousePressEvent(self, event):
        """
        On right-click, rotate the anchor by 90 degrees. Otherwise, allow normal drag/move behavior.
        """
        if event.button() == Qt.RightButton:
            self.rotate_90()
            event.accept()
        else:
            super().mousePressEvent(event)
    def __init__(self, pos, parent=None, side=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        # Try to load grip_size_px from theme, default to 5, radius is half
        try:
            import json
            with open("docs/theme_tokens.json") as f:
                theme = json.load(f)
            self.radius = float(theme.get("grip_size_px", 5)) / 2
        except Exception:
            self.radius = 2.5
        self.setPos(*pos)
        self.side = side  # 'a' or 'b'
        # Create two pins and two leaders as children of the anchor
        self.pins = []
        self.leaders = []
        # Theme color for default wire (grey_300)
        theme_grey = QColor("#D0D0D0")
        for i in range(2):
            pin = QGraphicsEllipseItem(-3, -3, 6, 6, self)  # 6px diameter circle
            pin.setBrush(QBrush(theme_grey))
            pin.setPen(Qt.NoPen)
            self.pins.append(pin)
            leader = QGraphicsLineItem(self)
            leader.setPen(QPen(theme_grey, 3, Qt.SolidLine))
            leader.setZValue(1)
            leader.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            self.leaders.append(leader)

    def hoverEnterEvent(self, event):
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.update()
        super().hoverLeaveEvent(event)

    def rotate_90(self):
        """
        Increment this anchor's rotation by 90 degrees (modulo 360),
        update the corresponding model field (rotation_a or rotation_b),
        and trigger a layout refresh on the parent TwistedPairItem.
        """
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

    def boundingRect(self):
        r = self.radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None):
        # Interaction palette: Drag > Selected > Hover > Default
        theme_grey = QColor("#D0D0D0")
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(theme_grey)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

    def itemChange(self, change, value):
        # Only trigger layout update after the position has actually changed
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
        self.color1 = QColor(Qt.red)
        self.color2 = QColor(Qt.blue)
        self._rect = QRectF(0, 0, 1, 1)

    def path(self):
        """
        Return the main helix path for compatibility with tests.
        """
        return self.path1

    def set_strand_colors(self, color1: QColor, color2: QColor):
        self.color1 = color1
        self.color2 = color2
        self.update()

    def update_geometry(self, start: QPointF, end: QPointF, elbows=None):
        if elbows is None:
            elbows = []
        self.prepareGeometryChange()
        amp = 5.0
        wavelength = 20.0
        points = [start] + elbows + [end]
        self.path1 = QPainterPath()
        self.path2 = QPainterPath()
        
        for i in range(len(points) - 1):
            p_start = points[i]
            p_end = points[i+1]
            s = (p_start.x(), p_start.y())
            e = (p_end.x(), p_end.y())
            strand1, strand2 = calculate_double_helix(s, e, amp, wavelength)
            
            if strand1:
                if i == 0:
                    self.path1.moveTo(QPointF(*strand1[0]))
                else:
                    self.path1.lineTo(QPointF(*strand1[0]))
                for pt in strand1[1:]:
                    self.path1.lineTo(QPointF(*pt))
            
            if strand2:
                if i == 0:
                    self.path2.moveTo(QPointF(*strand2[0]))
                else:
                    self.path2.lineTo(QPointF(*strand2[0]))
                for pt in strand2[1:]:
                    self.path2.lineTo(QPointF(*pt))
                    
        self._rect = self.path1.boundingRect().united(self.path2.boundingRect())

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color1, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path1)
        painter.setPen(QPen(self.color2, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path2)

class TwistedPairItem(QGraphicsObject):
    def __init__(self, model: TwistedPair, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.anchor_a = TwistAnchorItem(model.node_a, self, side='a')
        self.anchor_b = TwistAnchorItem(model.node_b, self, side='b')
        self.helix = DoubleHelixPathItem(self)
        self.elbow_handles = []
        self.update_layout()

    def update_layout(self):
        if not hasattr(self, "anchor_a") or not hasattr(self, "anchor_b"):
            return

        def snap_point(pt):
            return QPointF(round(pt.x() / 20) * 20, round(pt.y() / 20) * 20)

        def rotated_offsets(rotation):
            base = [QPointF(-20, 20), QPointF(-20, -20)]
            t = QTransform()
            t.rotate(rotation)
            return [t.map(offset) for offset in base]

        def points_close(p1, p2, eps=0.01):
            return (abs(p1.x() - p2.x()) < eps) and (abs(p1.y() - p2.y()) < eps)

        def color_for_wire(wire_id, default):
            if wire_id is None:
                return default
            if wire_id == 1:
                return QColor("blue")
            if wire_id == 2:
                return QColor("red")
            return default

        # Use explicit helix colors if set, otherwise fallback to model
        color1 = self.helix.color1 if self.helix.color1 != THEME_GREY else color_for_wire(getattr(self.model, 'wire_id_1', None), THEME_GREY)
        color2 = self.helix.color2 if self.helix.color2 != THEME_GREY else color_for_wire(getattr(self.model, 'wire_id_2', None), THEME_GREY)

        # Update Anchors
        for anchor, side_rot_attr in [(self.anchor_a, 'rotation_a'), (self.anchor_b, 'rotation_b')]:
            pos_scene = anchor.scenePos()
            snap_scene = snap_point(pos_scene)
            if not points_close(pos_scene, snap_scene):
                snap_local = self.mapFromScene(snap_scene)
                anchor.setPos(snap_local)
            
            rot = getattr(self.model, side_rot_attr, 0) % 360
            offsets = rotated_offsets(rot)
            
            for i, (pin, leader) in enumerate(zip(anchor.pins, anchor.leaders)):
                c = color1 if i == 0 else color2
                pin.setBrush(QBrush(c))
                leader.setPen(QPen(c, 3, Qt.SolidLine))
                pin.setPos(offsets[i])
                leader.setLine(0, 0, offsets[i].x(), offsets[i].y())

        # Sync Elbow Handles
        elbows_data = getattr(self.model, 'elbows', [])
        while len(self.elbow_handles) < len(elbows_data):
            handle = ElbowHandle(len(self.elbow_handles), self)
            self.elbow_handles.append(handle)
        while len(self.elbow_handles) > len(elbows_data):
            handle = self.elbow_handles.pop()
            handle.setParentItem(None)
            if handle.scene():
                handle.scene().removeItem(handle)

        for i, handle in enumerate(self.elbow_handles):
            handle.index = i
            pos = elbows_data[i]
            # Only update handle position if it's not the one currently driving the drag
            if not (handle.isSelected() or handle.isUnderMouse()):
                handle.setPos(QPointF(pos[0], pos[1]))

        # Update Helix
        self.helix.set_strand_colors(color1, color2)
        elbow_points = [QPointF(e[0], e[1]) for e in elbows_data]
        self.helix.update_geometry(self.anchor_a.pos(), self.anchor_b.pos(), elbow_points)

    def mouseDoubleClickEvent(self, event):
        scene_pos = event.scenePosition().toPointF() if hasattr(event, 'scenePosition') else event.scenePos()
        pos = self.mapFromScene(scene_pos)
        
        points = [self.anchor_a.pos()] + [QPointF(e[0], e[1]) for e in self.model.elbows] + [self.anchor_b.pos()]
        min_dist = float('inf')
        insert_idx = 0
        
        for i in range(len(points) - 1):
            a, b = points[i], points[i+1]
            ab = b - a
            ab_len2 = ab.x()**2 + ab.y()**2
            if ab_len2 == 0:
                t = 0
            else:
                t = max(0, min(1, ((pos - a).x()*ab.x() + (pos - a).y()*ab.y()) / ab_len2))
            proj = a + ab * t
            dist = (proj - pos).manhattanLength()
            if dist < min_dist:
                min_dist = dist
                insert_idx = i
        
        self.model.elbows.insert(insert_idx, (pos.x(), pos.y()))
        self.update_layout()
        event.accept()

    def set_signal(self, pin_item, wire_id, color):
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
            side = 'a'
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
            side = 'b'
        else:
            raise ValueError("Pin not found in anchors")

        if idx == 0:
            self.model.wire_id_1 = wire_id
            self.helix.color1 = QColor(color)
        elif idx == 1:
            self.model.wire_id_2 = wire_id
            self.helix.color2 = QColor(color)

        self.helix.update()
        self.update_layout()

    def get_signal(self, pin_item):
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            raise ValueError("Pin not found in anchors")
        if idx == 0:
            return self.model.wire_id_1
        elif idx == 1:
            return self.model.wire_id_2
        return None

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass

class ElbowHandle(QGraphicsItem):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # CRITICAL: This flag enables itemChange notifications during drag
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.radius = 2.5
        self.setZValue(2)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, 2*r, 2*r)

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.State_Sunken:
            brush = QBrush(Qt.red)
        elif option.state & QStyle.State_Selected:
            brush = QBrush(Qt.darkBlue)
        elif option.state & QStyle.State_MouseOver:
            brush = QBrush(QColor('orange'))
        else:
            brush = QBrush(THEME_GREY)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                elbows = parent.model.elbows
                if 0 <= self.index < len(elbows):
                    # Update model with new position
                    elbows[self.index] = (self.pos().x(), self.pos().y())
                    # Trigger redraw of the wire
                    parent.update_layout()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            parent = self.parentItem()
            if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
                if 0 <= self.index < len(parent.model.elbows):
                    del parent.model.elbows[self.index]
                    parent.update_layout()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()
        # If any model update is needed, access via parent
        parent = self.parentItem()
        if parent and hasattr(parent, 'model') and hasattr(parent, 'update_layout'):
            parent.update_layout()

        class TwistAnchorItem(QGraphicsItem):
            def __init__(self, pos, parent=None, side=None):
                super().__init__(parent)
                self.setFlag(QGraphicsItem.ItemIsMovable, True)
                self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                self.setFlag(QGraphicsItem.ItemIsSelectable, True)
                self.setAcceptHoverEvents(True)
                self.setZValue(2)
        
                # Default size matching theme (5px diameter)
                self.radius = 2.5
                self.setPos(*pos)
                self.side = side  # 'a' or 'b'
        
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
                    # Ensure leaders draw behind the anchor grip
                    leader.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
                    self.leaders.append(leader)

            def mousePressEvent(self, event):
                if event.button() == Qt.RightButton:
                    self.rotate_90()
                    event.accept()
                else:
                    super().mousePressEvent(event)

            def mouseReleaseEvent(self, event):
                super().mouseReleaseEvent(event)
                self.update()

            def hoverEnterEvent(self, event):
                self.update()
                super().hoverEnterEvent(event)

            def hoverLeaveEvent(self, event):
                self.update()
                super().hoverLeaveEvent(event)

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

            def boundingRect(self):
                r = self.radius
                # Inflate bounding rect slightly to avoid rendering artifacts
                return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

            def paint(self, painter, option, widget=None):
                if option.state & QStyle.State_Sunken:
                    brush = QBrush(Qt.red)
                elif option.state & QStyle.State_Selected:
                    brush = QBrush(Qt.darkBlue)
                elif option.state & QStyle.State_MouseOver:
                    brush = QBrush(QColor('orange'))
                else:
                    brush = QBrush(THEME_GREY)
                painter.setBrush(brush)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius))

            def itemChange(self, change, value):
                if change == QGraphicsItem.ItemPositionHasChanged:
                    parent = self.parentItem()
                    if parent and hasattr(parent, "update_layout"):
                        parent.update_layout()
                return super().itemChange(change, value)
        # Use childrenBoundingRect to avoid rendering artifacts

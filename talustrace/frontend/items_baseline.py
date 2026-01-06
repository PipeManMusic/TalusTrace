import json
import html
import math
from pathlib import Path
from collections import defaultdict

from PySide6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QMenu,
    QGraphicsEllipseItem,
    QMessageBox,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QColorDialog,
)
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QFontMetricsF, QAction, QPainterPath, QPainterPathStroker, QPainter
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, QTimer
from talustrace.backend.models import Side, Pin as PinModel
from talustrace.backend.sizer import AutoSizer
from talustrace.backend.printer import Printer
from talustrace.backend.labels import LabelManager
import os

# Debugging flag (set TALUSTRACE_HANDLE_DEBUG=1 to enable verbose handle debug prints)
HANDLE_DEBUG = bool(os.environ.get('TALUSTRACE_HANDLE_DEBUG'))
HANDLE_DEBUG_VERBOSE = bool(os.environ.get('TALUSTRACE_HANDLE_DEBUG_VERBOSE'))

# Visual Constants
GRID_SIZE = 20
BOX_COLOR = QColor(50, 50, 50)
BORDER_COLOR = QColor(200, 200, 200)
SELECTED_COLOR = QColor(255, 165, 0)
TEXT_COLOR = QColor(255, 255, 255)

PIN_COLOR = QColor(200, 200, 200)
PIN_HOVER_COLOR = QColor(0, 255, 0)
PIN_PITCH = 20
ELBOW_COLOR = QColor(0, 122, 255)
# Pivot color (dark blue) used for unselected control pivot fill
PIVOT_COLOR = QColor(0, 70, 140)
SEGMENT_HANDLE_COLOR = QColor(180, 180, 180)
TEXT_INSET = 6
WIRE_THICKNESS = 3  # Shared thickness for wires and leader lines
# Control pivot visual sizes
CONTROL_PIVOT_DIAM = 10  # diameter in device pixels for control pivot ellipse (fixed device-space size)
CONTROL_DOT_DIAM = 6     # diameter of the small always-visible dot
PIVOT_HIT_RADIUS = 16  # Scene-pixel radius around pivot that counts as clicking the grip

# Selection visuals for making the pivot unambiguous
SELECTED_RING_PAD = 5        # extra radius (device pixels) around pivot for the selection ring
SELECTED_RING_WIDTH = 3      # pen width for selection ring
SELECTED_LABEL_TEXT = "Pivot"

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configure.json"
CONFIG_USAGE_KEY = "context_menu_usage"
_ACTION_USAGE = defaultdict(int)


def _load_usage():
    try:
        data = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
        usage = data.get(CONFIG_USAGE_KEY, {})
        for k, v in usage.items():
            if isinstance(v, int):
                _ACTION_USAGE[k] = v
    except Exception:
        pass


def _save_usage():
    try:
        data = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    except Exception:
        data = {}
    data[CONFIG_USAGE_KEY] = {k: int(v) for k, v in _ACTION_USAGE.items()}
    try:
        CONFIG_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _record_action_usage(key: str):
    _ACTION_USAGE[key] += 1
    _save_usage()


def _usage_rank(key: str) -> int:
    return _ACTION_USAGE.get(key, 0)


def _make_action(menu: QMenu, text: str, slot, usage_key: str) -> QAction:
    act = QAction(text, menu)

    def _handler(checked=False):
        _record_action_usage(usage_key)
        slot()

    act.triggered.connect(_handler)
    return act


_load_usage()


class PinEditDialog(QDialog):
    def __init__(self, pin_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Pin")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_edit = QLineEdit(pin_model.id)
        form.addRow("Pin ID", self.id_edit)

        self.label_edit = QLineEdit(pin_model.label or "")
        form.addRow("Pin Label", self.label_edit)

        self.side_combo = QComboBox()
        for side in Side:
            self.side_combo.addItem(side.value.title(), side)
        if pin_model.side in Side:
            self.side_combo.setCurrentIndex(list(Side).index(pin_model.side))
        form.addRow("Side", self.side_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        new_id = self.id_edit.text().strip()
        new_label_raw = self.label_edit.text().strip()
        new_label = new_label_raw if new_label_raw else None
        new_side = self.side_combo.currentData()
        return new_id, new_label, new_side


class DeviceEditDialog(QDialog):
    def __init__(self, device_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Device")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_edit = QLineEdit(device_model.id)
        form.addRow("Device ID", self.id_edit)

        self.label_edit = QLineEdit(device_model.label or "")
        form.addRow("Label", self.label_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        new_id = self.id_edit.text().strip()
        new_label_raw = self.label_edit.text().strip()
        new_label = new_label_raw if new_label_raw else None
        return new_id, new_label


class PinItem(QGraphicsRectItem):
    def __init__(self, pin_model, parent=None):
        super().__init__(parent)
        self.model = pin_model
        # Enlarge pick box for easier hover/selection and context menu access.
        # Restore visual pin geometry (small line + tip), but keep leader lines removed
        # This makes pins visible in renders while not drawing leader lines that previously inflated bounds.
        self.setRect(-8, -8, 16, 16)
        self.setBrush(Qt.NoBrush)
        self.setPen(Qt.NoPen)
        # Visual line from head to tail
        self.line = QGraphicsLineItem(self)
        self.line.setPen(QPen(PIN_COLOR, WIRE_THICKNESS))
        # Visual tip circle at the end of the pin line
        self.tip = QGraphicsEllipseItem(-3, -3, 6, 6, self)
        self.tip.setBrush(QBrush(PIN_COLOR))
        self.tip.setPen(Qt.NoPen)
        self.tip.setZValue(1)
        self.setAcceptHoverEvents(True)
        # Leader line connects the pin tail to the node control pivot.
        # It is drawn as a child of the node so coordinates are in node-local space.
        try:
            parent_item = parent or self.parentItem()
            if parent_item is not None:
                self.leader = QGraphicsLineItem(parent_item)
                self.leader.setPen(QPen(PIN_COLOR, WIRE_THICKNESS))
                self.leader.setZValue(0)
            else:
                self.leader = None
        except Exception:
            self.leader = None
        # Keep hover flag for compatibility
        self._hovered = False
        # Track the current visual color for the pin so hover leave can restore it
        self._pending_color = PIN_COLOR

    def set_visual_geometry(self, x1, y1, x2, y2):
        # Set head (local) position and snap to grid
        self.setPos(x1, y1)
        try:
            head_scene = self.mapToScene(0, 0)
            snapped_scene = QPointF(round(head_scene.x() / GRID_SIZE) * GRID_SIZE, round(head_scene.y() / GRID_SIZE) * GRID_SIZE)
            new_local = self.parentItem().mapFromScene(snapped_scene) if self.parentItem() else snapped_scene
            self.setPos(new_local)
            # Ensure head is centered on a grid intersection (both X and Y)
            head_scene = self.mapToScene(0, 0)
            head_snapped = QPointF(round(head_scene.x() / GRID_SIZE) * GRID_SIZE, round(head_scene.y() / GRID_SIZE) * GRID_SIZE)
            if head_snapped != head_scene:
                new_local2 = self.parentItem().mapFromScene(head_snapped) if self.parentItem() else head_snapped
                self.setPos(new_local2)
        except Exception:
            pass
        # Recompute line to tail based on snapped head local position
        # Tail (tip) should be snapped to the global grid in scene coordinates to keep it aligned.
        try:
            # Tail should point from the head toward the bundle (pivot) by a short stub
            side = getattr(self.model, 'side', None)
            tip_off = 6.0
            try:
                parent = self.parentItem() or self
                head_scene = parent.mapToScene(self.pos())
                pivot_scene = parent.mapToScene(getattr(parent, '_pivot', parent._rect.center()))
                vec_x = pivot_scene.x() - head_scene.x()
                vec_y = pivot_scene.y() - head_scene.y()
                length = (vec_x * vec_x + vec_y * vec_y) ** 0.5
                if length == 0:
                    # fallback axis-aligned stub based on side
                    if side == Side.LEFT:
                        vec_x, vec_y = -1.0, 0.0
                    elif side == Side.RIGHT:
                        vec_x, vec_y = 1.0, 0.0
                    elif side == Side.TOP:
                        vec_x, vec_y = 0.0, -1.0
                    elif side == Side.BOTTOM:
                        vec_x, vec_y = 0.0, 1.0
                    else:
                        vec_x, vec_y = -1.0, 0.0
                    length = 1.0
                ux = vec_x / length
                uy = vec_y / length
                # Compute tail scene position a small distance toward pivot
                tail_scene = QPointF(head_scene.x() + ux * tip_off, head_scene.y() + uy * tip_off)
                tail_local = parent.mapFromScene(tail_scene)
                dx = tail_local.x() - self.pos().x()
                dy = tail_local.y() - self.pos().y()
            except Exception:
                # fallback to previous approach
                dx = x2 - self.pos().x()
                dy = y2 - self.pos().y()
        except Exception:
            dx = x2 - self.pos().x()
            dy = y2 - self.pos().y()

        try:
            self.line.setLine(0, 0, dx, dy)
        except Exception:
            pass
        # Place head ellipse at the local origin (head) and keep tip as the line end (tail)
        try:
            self.tip.setPos(0, 0)
        except Exception:
            pass
        # Update leader/visual color if attached to a bundle
        try:
            # Keep existing color unless bundle has overridden it via set_color
            if hasattr(self, '_pending_color') and isinstance(self._pending_color, QColor):
                self.set_color(self._pending_color)
        except Exception:
            pass
        # Update leader line
        try:
            self.update_leader()
        except Exception:
            pass

    def set_color(self, color: QColor):
        try:
            if not isinstance(color, QColor):
                return
            self.line.setPen(QPen(color, WIRE_THICKNESS))
            self.tip.setBrush(QBrush(color))
            if self.leader:
                self.leader.setPen(QPen(color, WIRE_THICKNESS))
            # Store pending color so future geometry updates can reapply
            self._pending_color = color
        except Exception:
            pass

    def hoverEnterEvent(self, event):
        try:
            self.line.setPen(QPen(PIN_HOVER_COLOR, WIRE_THICKNESS))
            self.tip.setBrush(QBrush(PIN_HOVER_COLOR))
            self.tip.setScale(1.2)
        except Exception:
            pass
        self._hovered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        try:
            # Restore the pin's previous color (may be bundle-applied) and the standard wire thickness
            color = getattr(self, '_pending_color', PIN_COLOR)
            self.line.setPen(QPen(color, WIRE_THICKNESS))
            self.tip.setBrush(QBrush(color))
            self.tip.setScale(1.0)
            # Also restore leader pen if present
            if self.leader:
                try:
                    self.leader.setPen(QPen(color, WIRE_THICKNESS))
                except Exception:
                    pass
        except Exception:
            pass
        self._hovered = False
        super().hoverLeaveEvent(event)

    def update_leader(self):
        """Update the leader line from this pin's tail (line end) to the parent node's control pivot (node._pivot).
        The leader is drawn as a child of the node so coordinates are set in node-local space."""
        try:
            node = self.parentItem()
            if not node or not hasattr(node, '_pivot') or not self.leader:
                return
            tail_scene = self.get_tail_scene_pos()
            # tail in node-local coords
            tail_local = node.mapFromScene(tail_scene)
            # Compute pivot in scene coords then map back to node-local to ensure consistency
            pivot_scene = node.mapToScene(getattr(node, '_pivot', node._rect.center()))
            pivot_local = node.mapFromScene(pivot_scene)

            self.leader.setLine(tail_local.x(), tail_local.y(), pivot_local.x(), pivot_local.y())
        except Exception:
            pass

    def get_scene_pos(self):
        return self.mapToScene(0, 0)

    def get_tip_scene_pos(self):
        # Tip (head) is the ellipse at the pin head; return its scene coordinates
        try:
            return self.tip.mapToScene(self.tip.boundingRect().center())
        except Exception:
            try:
                return self.mapToScene(0, 0)
            except Exception:
                return self.mapToScene(0, 0)

    def get_tail_scene_pos(self):
        # Tail is the end of the pin's line; return its scene coordinates
        try:
            p2 = self.line.line().p2()
            return self.mapToScene(p2)
        except Exception:
            try:
                # Fallback to head
                return self.get_tip_scene_pos()
            except Exception:
                return self.mapToScene(0, 0)

    def contextMenuEvent(self, event):
        menu = QMenu()
        entries = [
            ("pin.delete", "Delete Pin", self._delete_pin_confirm),
            ("pin.edit", "Edit Pin...", self._edit_pin),
        ]
        for key, text, slot in sorted(entries, key=lambda e: (-_usage_rank(e[0]), entries.index(e))):
            menu.addAction(_make_action(menu, text, slot, key))
        menu.exec(event.screenPos())

    def _delete_pin_confirm(self):
        parent = self.parentItem()
        if not parent or not hasattr(parent, "delete_pin"):
            return
        label = self.model.label or self.model.id
        resp = QMessageBox.question(
            None,
            "Delete Pin",
            f"Delete pin '{label}'?\nAttached wires will be removed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            parent.delete_pin(self)

    def _edit_pin(self):
        parent = self.parentItem()
        if parent and hasattr(parent, "edit_pin"):
            parent.edit_pin(self)

    def set_meta(self, meta: dict):
        self.model.meta = meta or {}
        parent = self.parentItem()
        if parent and hasattr(parent, "notify_pin_meta_changed"):
            parent.notify_pin_meta_changed(self)

class DeviceItem(QGraphicsItem):
    def __init__(self, device_model, on_changed=None, on_delete_device=None, on_delete_pin=None):
        super().__init__()
        self.model = device_model
        self.on_changed = on_changed
        self.on_delete_device = on_delete_device
        self.on_delete_pin = on_delete_pin
        self.attached_wires = []
        self.pins = {}
        self.pin_text_items = {}
        self._rect = QRectF()
        self._brush = QBrush(BOX_COLOR)
        self._pen = QPen(BORDER_COLOR, 2)
        self._side_highlight = None
        
        # Removed ItemIsMovable to handle manual snapping/moving
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        
        # Removed rectangular halo; selection visuals should use the control pivot ellipse where applicable
        self.halo = None

        self.id_text = QGraphicsSimpleTextItem(f"({self.model.id})", self)
        self.id_text.setBrush(QBrush(TEXT_COLOR))
        self.id_text.setFont(QFont('Arial', 8))

        self.label = QGraphicsSimpleTextItem(self.model.label, self)
        self.label.setBrush(QBrush(TEXT_COLOR))
        self.label.setFont(QFont('Arial', 10, QFont.Bold))
        self.layout_pins()
        self.setPos(self._snap(self.model.x), self._snap(self.model.y))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If a handle (segment/elbow) is on top at this location, let it handle the event instead
            try:
                items = self.scene().items(event.scenePos())
                for it in items:
                    if it is self:
                        continue
                    if it.__class__.__name__ in ('SegmentHandle', 'ElbowHandle'):
                        event.ignore()
                        return
            except Exception:
                pass

            self._drag_start_pos = event.scenePos()
            self._item_start_pos = self.pos()
            # Don't accept yet, let super handle selection
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Only move if we have a valid drag start position AND the left button is held down
        if hasattr(self, '_drag_start_pos') and (event.buttons() & Qt.LeftButton):
            # Manual Move with Snap
            delta = event.scenePos() - self._drag_start_pos
            new_pos = self._item_start_pos + delta
            new_pos.setX(self._snap(new_pos.x()))
            new_pos.setY(self._snap(new_pos.y()))
            self.setPos(new_pos)
            
            # Manually update dependents since ItemSendsGeometryChanges is off
            # self.halo.setPos(new_pos)
            # self.model.x, self.model.y = new_pos.x(), new_pos.y()
            # for wire in self.attached_wires: wire.update_geometry()
            
            # Accept the event so it doesn't propagate
            event.accept()
        else:
            # If we are not dragging, let the base class handle it (e.g. for hover events)
            # super().mouseMoveEvent(event)
            event.ignore()

    def mouseReleaseEvent(self, event):
        if hasattr(self, '_drag_start_pos'):
            del self._drag_start_pos
            del self._item_start_pos
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        pass
    def contextMenuEvent(self, event):
        menu = QMenu()

        entries = [
            ("device.delete", "Delete Device", self._delete_device_confirm),
            ("device.edit", "Edit Device...", self._edit_device),
            ("device.print", "Print Label", self.print_label),
            ("device.suggest", "Suggest Short Code", self._apply_label_suggestion),
            ("device.bulk_add", "Bulk Add Pins...", self._prompt_bulk_pins),
        ]

        # Sort top-level actions by usage (desc) then original order for stability.
        for key, text, slot in sorted(entries, key=lambda e: (-_usage_rank(e[0]), entries.index(e))):
            menu.addAction(_make_action(menu, text, slot, key))

        add_pin_menu = menu.addMenu("Add Pin")
        side_entries = [(f"device.add_pin.{side.value}", f"{side.value.title()}", side) for side in [Side.LEFT, Side.RIGHT, Side.TOP, Side.BOTTOM]]
        for key, text, side in sorted(side_entries, key=lambda e: (-_usage_rank(e[0]), side_entries.index(e))):
            def _add(checked=False, side=side, key=key):
                _record_action_usage(key)
                self._add_pin_quick(side)
            act_side = QAction(text, add_pin_menu)
            act_side.triggered.connect(_add)
            add_pin_menu.addAction(act_side)

        menu.exec(event.screenPos())

    def _delete_device_confirm(self):
        if not self.on_delete_device:
            return
        resp = QMessageBox.question(
            None,
            "Delete Device",
            f"Delete device '{self.model.label or self.model.id}'?\nAttached wires will be removed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.on_delete_device(self)

    def delete_pin(self, pin_item: PinItem):
        if not pin_item or not self.on_delete_pin:
            return
        self.on_delete_pin(self, pin_item)

    def notify_pin_meta_changed(self, pin_item: PinItem):
        # Recompute metadata on all attached wires involving this pin
        for wire in list(self.attached_wires):
            if wire.src_pin_id == pin_item.model.id or wire.tgt_pin_id == pin_item.model.id:
                wire.refresh_metadata()
                wire._notify_changed()
    def print_label(self):
        p = Printer()
        p.print_label(self.model.label)
    def _apply_label_suggestion(self):
        suggestion = self.suggest_code()
        if not suggestion:
            return
        resp = QMessageBox.question(
            None,
            "Apply Short Code",
            f"Apply suggested code '{suggestion}' to this device label?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp == QMessageBox.Yes:
            self.set_label(suggestion)
    def suggest_code(self):
        base = self.model.label or "DEVICE"
        return LabelManager.generate_short_code(base)
    def _edit_device(self):
        self.edit_device()
    def set_label(self, text: str):
        self.model.label = text
        self.label.setText(text)
        self.layout_pins()
        if callable(self.on_changed):
            self.on_changed()

    def edit_device(self):
        dlg = DeviceEditDialog(self.model)
        if dlg.exec() != QDialog.Accepted:
            return

        new_id, new_label = dlg.values()
        if not new_id:
            return

        # Prevent duplicate device IDs in the same scene
        if self.scene():
            for item in self.scene().items():
                if isinstance(item, DeviceItem) and item is not self and item.model.id == new_id:
                    QMessageBox.warning(None, "Device ID Exists", f"Device ID '{new_id}' already exists.")
                    return

        self.apply_device_edit(new_id, new_label)

    def apply_device_edit(self, new_id: str, new_label: str | None):
        old_id = self.model.id
        self.model.id = new_id
        self.id_text.setText(f"({new_id})")
        label_to_set = new_label if new_label else new_id
        self.set_label(label_to_set)
        self._update_wire_device_refs(old_id, new_id)

    def _update_wire_device_refs(self, old_id: str, new_id: str):
        if old_id == new_id:
            return
        for wire in self.attached_wires:
            if wire.model.from_conn.startswith(f"{old_id}."):
                pin = wire.model.from_conn.split('.')[1]
                wire.model.from_conn = f"{new_id}.{pin}"
            if wire.model.to_conn.startswith(f"{old_id}."):
                pin = wire.model.to_conn.split('.')[1]
                wire.model.to_conn = f"{new_id}.{pin}"
            wire.src_pin_id = wire.model.from_conn.split('.')[1]
            wire.tgt_pin_id = wire.model.to_conn.split('.')[1]
            wire.update_geometry()

    def _format_pin_text(self, pin_model) -> str:
        if pin_model.label and pin_model.label != pin_model.id:
            return f"{pin_model.id} {pin_model.label}"
        return str(pin_model.id)

    # --- Pin editing helpers ---
    def _next_pin_id(self):
        existing = [p.id for p in self.model.pins] if isinstance(self.model.pins, list) else []
        nums = [int(pid) for pid in existing if pid.isdigit()]
        next_num = (max(nums) + 1) if nums else (len(existing) + 1)
        return str(next_num)

    def add_pin_model(self, side: Side, label: str | None = None, pin_id: str | None = None):
        if not isinstance(self.model.pins, list):
            self.model.pins = []
        pid = pin_id or self._next_pin_id()
        from talustrace.backend.models import Pin as PinModel
        pin_model = PinModel(id=pid, label=label, side=side)
        self.model.pins.append(pin_model)
        self.layout_pins()
        if callable(self.on_changed):
            self.on_changed()

    def edit_pin(self, pin_item: PinItem):
        pin_model = pin_item.model
        dlg = PinEditDialog(pin_model)
        if dlg.exec() != QDialog.Accepted:
            return

        new_id, new_label, new_side = dlg.values()
        if not new_id:
            return
        if any(p.id == new_id and p is not pin_model for p in self.model.pins):
            QMessageBox.warning(None, "Pin ID Exists", f"Pin ID '{new_id}' already exists on this device.")
            return

        self.apply_pin_edit(pin_item, new_id, new_label, new_side)

    def apply_pin_edit(self, pin_item: PinItem, new_id: str, new_label: str | None, new_side: Side):
        from talustrace.backend.models import Pin as PinModel
        pin_model = pin_item.model
        old_id = pin_model.id

        if any(p.id == new_id and p is not pin_model for p in self.model.pins):
            return

        label_to_set = new_label if new_label else new_id
        new_pin = PinModel(id=new_id, label=label_to_set, side=new_side)
        for idx, p in enumerate(self.model.pins):
            if p is pin_model:
                self.model.pins[idx] = new_pin
                break

        self.layout_pins()
        self._update_wire_pin_refs(old_id, new_id)

        if callable(self.on_changed):
            self.on_changed()

    def _update_wire_pin_refs(self, old_id: str, new_id: str):
        if old_id == new_id:
            return
        for wire in self.attached_wires:
            if wire.src_pin_id == old_id:
                wire.src_pin_id = new_id
                wire.model.from_conn = f"{self.model.id}.{new_id}"
            if wire.tgt_pin_id == old_id:
                wire.tgt_pin_id = new_id
                wire.model.to_conn = f"{self.model.id}.{new_id}"
            wire.update_geometry()

    def _add_pin_quick(self, side: Side):
        pid = self._next_pin_id()
        self.add_pin_model(side=side, label=None, pin_id=pid)
        self._flash_side_highlight(side)

    def _prompt_bulk_pins(self):
        count, ok = QInputDialog.getInt(None, "Bulk Add Pins", "How many pins?", 2, 1, 512, 1)
        if not ok:
            return
        # starting side LEFT, alternate L/R
        for i in range(count):
            side = Side.LEFT if i % 2 == 0 else Side.RIGHT
            pid = self._next_pin_id()
            self.add_pin_model(side=side, label=None, pin_id=pid)
    def layout_pins(self):
        # Remove existing pin graphics before rebuild; ensure we also remove any
        # leader lines that are children of the node so they don't persist as stray geometry.
        for pin in self.pins.values():
            try:
                # Remove leader first
                if getattr(pin, 'leader', None) and pin.leader.scene():
                    pin.leader.scene().removeItem(pin.leader)
            except Exception:
                pass
            try:
                if pin.scene():
                    pin.scene().removeItem(pin)
            except Exception:
                pass
        self.pins = {}

        # Use Backend AutoSizer for dimensions
        width, height = AutoSizer.calculate_size(self.model)
        
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, width, height)
        if getattr(self, 'halo', None) is not None:
            self.halo.setRect(self._rect.adjusted(-2, -2, 2, 2))
        
        id_br = self.id_text.boundingRect()
        lb = self.label.boundingRect()

        label_y = (height - (lb.height() + id_br.height() + 4)) / 2
        self.label.setPos((width - lb.width()) / 2, label_y)

        id_y = label_y + lb.height() + 4
        self.id_text.setPos((width - id_br.width()) / 2, id_y)
        
        pins = self.model.pins if isinstance(self.model.pins, list) else []
        p_left = [p for p in pins if p.side == Side.LEFT]
        p_right = [p for p in pins if p.side == Side.RIGHT]
        p_top = [p for p in pins if p.side == Side.TOP]
        p_bottom = [p for p in pins if p.side == Side.BOTTOM]
        
        def add_pin(pin_data, x1, y1, x2, y2):
            pin = PinItem(pin_data, self)
            pin.set_visual_geometry(x1, y1, x2, y2)
            self.pins[pin_data.id] = pin
            
        # Pin Layout Logic (Should match AutoSizer assumptions)
        for item in self.pin_text_items.values():
            if item.scene():
                item.scene().removeItem(item)
        self.pin_text_items = {}

        # Prepare text metrics for pin labels so we can center them in their columns.
        pin_font = QFont('Arial', 9)

        def measure_text(text: str):
            probe = QGraphicsSimpleTextItem(text)
            probe.setFont(pin_font)
            br = probe.boundingRect()
            return br.width(), br.height()

        def formatted_width(pin_list):
            if not pin_list:
                return 0, 0
            widths, heights = zip(*(measure_text(self._format_pin_text(p)) for p in pin_list))
            return max(widths), max(heights)

        left_max_w, left_max_h = formatted_width(p_left)
        right_max_w, right_max_h = formatted_width(p_right)
        top_max_w, top_max_h = formatted_width(p_top)
        bottom_max_w, bottom_max_h = formatted_width(p_bottom)

        top_padding = (top_max_h + PIN_PITCH + 6) if p_top else 10
        bottom_padding = (bottom_max_h + PIN_PITCH + 6) if p_bottom else 10

        # Position the label block centered within the available height, leaving space for top/bottom pins.
        label_block_h = lb.height() + id_br.height() + 4
        avail_h = max(height - top_padding - bottom_padding, 0)
        label_top = top_padding + max((avail_h - label_block_h) / 2, 0)

        self.label.setPos((width - lb.width()) / 2, label_top)
        id_y = label_top + lb.height() + 4
        self.id_text.setPos((width - id_br.width()) / 2, id_y)

        label_block_bottom = id_y + id_br.height()
        label_center_y = label_top + (label_block_h / 2)

        lr_count = max(len(p_left), len(p_right))
        lr_span = (lr_count - 1) * PIN_PITCH if lr_count > 0 else 0

        region_top = top_padding
        region_bottom = height - bottom_padding
        region_bottom = max(region_top, region_bottom)

        ideal_top = label_center_y - (lr_span / 2)
        lr_top = max(region_top, min(ideal_top, region_bottom - lr_span))

        # Snap to grid while respecting bounds
        snapped_top = round(lr_top / GRID_SIZE) * GRID_SIZE
        if snapped_top < region_top:
            snapped_top = region_top
        if snapped_top > region_bottom - lr_span:
            snapped_top = region_bottom - lr_span
        lr_top = snapped_top

        left_text_left = TEXT_INSET
        right_text_right = width - TEXT_INSET

        def place_pin_text(pin_data, x_anchor, y_center, align):
            text = self._format_pin_text(pin_data)
            txt_item = QGraphicsSimpleTextItem(text, self)
            txt_item.setFont(pin_font)
            txt_item.setBrush(QBrush(TEXT_COLOR))
            br = txt_item.boundingRect()

            if align == "right":
                x_pos = x_anchor - br.width()
            elif align == "left":
                x_pos = x_anchor
            else:
                x_pos = x_anchor - br.width() / 2

            txt_item.setPos(x_pos, y_center - br.height() / 2)
            self.pin_text_items[(pin_data.side, pin_data.id)] = txt_item

        for i, p in enumerate(p_left):
            y = lr_top + (i * PIN_PITCH)
            add_pin(p, 0, y, -5, y)
            place_pin_text(p, left_text_left, y, "left")

        for i, p in enumerate(p_right):
            y = lr_top + (i * PIN_PITCH)
            add_pin(p, width, y, width + 5, y)
            place_pin_text(p, right_text_right, y, "right")

        if p_top:
            spacing = (width - (2 * GRID_SIZE)) / (len(p_top) + 1)
            top_text_y = (top_padding - top_max_h) / 2 if top_padding > top_max_h else top_max_h / 2
            for i, p in enumerate(p_top):
                x = GRID_SIZE + ((i + 1) * spacing)
                add_pin(p, x, 0, x, -5)
                place_pin_text(p, x, top_text_y, "center")

        if p_bottom:
            spacing = (width - (2 * GRID_SIZE)) / (len(p_bottom) + 1)
            bottom_text_y = height - bottom_padding + ((bottom_padding - bottom_max_h) / 2 if bottom_padding > bottom_max_h else bottom_max_h / 2)
            for i, p in enumerate(p_bottom):
                x = GRID_SIZE + ((i + 1) * spacing)
                add_pin(p, x, height, x, height + 5)
                place_pin_text(p, x, bottom_text_y, "center")

        # Update attached wires after layout changes
        for wire in self.attached_wires:
            wire.update_geometry()

    def boundingRect(self):
        return self._rect

    # Backward compatibility for tests expecting QGraphicsRectItem API
    def rect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        # Manually draw the device box to avoid any default selection behavior issues
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(self._rect)

        if self._side_highlight:
            hl_pen = QPen(QColor(0, 170, 255), 4)
            if self._side_highlight == Side.LEFT:
                painter.drawLine(self._rect.topLeft(), self._rect.bottomLeft())
            elif self._side_highlight == Side.RIGHT:
                painter.drawLine(self._rect.topRight(), self._rect.bottomRight())
            elif self._side_highlight == Side.TOP:
                painter.drawLine(self._rect.topLeft(), self._rect.topRight())
            elif self._side_highlight == Side.BOTTOM:
                painter.drawLine(self._rect.bottomLeft(), self._rect.bottomRight())
            painter.setPen(self._pen)

    def _snap(self, value): return round(value / GRID_SIZE) * GRID_SIZE
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneChange:
            if value and getattr(self, 'halo', None) is not None:
                value.addItem(self.halo)
            elif getattr(self, 'halo', None) and self.halo.scene():
                self.halo.scene().removeItem(self.halo)

        # Do not display rectangular halos; selection visuals (where needed) are handled
        # at the node level using a control pivot ellipse.

        if change == QGraphicsItem.ItemPositionHasChanged:
             # Keep model coordinates and attached wires in sync
             self.model.x, self.model.y = self.pos().x(), self.pos().y()
             for wire in self.attached_wires: wire.update_geometry()

        return super().itemChange(change, value)

    def _flash_side_highlight(self, side: Side):
        self._side_highlight = side
        self.update()
        QTimer.singleShot(600, self._clear_side_highlight)

    def _clear_side_highlight(self):
        self._side_highlight = None
        self.update()

    def _enforce_pin_grid(self):
        """Snap pin head positions to the global GRID_SIZE so that pin tips remain grid-locked.
        This adjusts the pin local position and recomputes the leader line to preserve the tail anchor."""
        for pid, pin in list(self.pins.items()):
            try:
                # Determine current pin head scene position and snap horizontally to GRID while preserving Y
                head_scene = pin.mapToScene(0, 0)
                # Preserve Y (so we move the entire pin horizontally), but snap X to nearest grid
                snapped_x = round(head_scene.x() / GRID_SIZE) * GRID_SIZE
                snapped_scene = QPointF(snapped_x, head_scene.y())

                # If this node has a defined pivot/bundle side, enforce that the pin head
                # lies exactly one GRID unit away from the pivot along the outward axis.
                try:
                    side = getattr(self, '_bundle_side', None)
                    if not side and getattr(self, 'bundle_refs', None):
                        b = self.bundle_refs[0]
                        other = b.source_node if b.target_node is self else b.target_node
                        vec = other.pos() - self.pos()
                        if abs(vec.x()) >= abs(vec.y()):
                            side = Side.RIGHT if vec.x() > 0 else Side.LEFT
                        else:
                            side = Side.BOTTOM if vec.y() > 0 else Side.TOP
                except Exception:
                    side = getattr(self, '_bundle_side', None)

                try:
                    if hasattr(self, '_pivot') and side is not None:
                        pivot_scene = self.mapToScene(self._pivot)
                        # For LEFT/RIGHT nodes, enforce H above and L below the pivot by one GRID unit.
                        if side in (Side.LEFT, Side.RIGHT):
                            if side == Side.LEFT:
                                snapped_scene.setX(pivot_scene.x() + GRID_SIZE)
                            else:
                                snapped_scene.setX(pivot_scene.x() - GRID_SIZE)
                            # Enforce vertical offset for H / L pins
                            if pid == 'H':
                                snapped_scene.setY(pivot_scene.y() - GRID_SIZE)
                            elif pid == 'L':
                                snapped_scene.setY(pivot_scene.y() + GRID_SIZE)
                        else:
                            # For TOP/BOTTOM, preserve previous behavior (align along outward axis)
                            if side == Side.TOP:
                                snapped_scene.setY(pivot_scene.y() + GRID_SIZE)
                            elif side == Side.BOTTOM:
                                snapped_scene.setY(pivot_scene.y() - GRID_SIZE)
                except Exception:
                    pass

                # Map snapped scene point back to node-local coords
                new_local = self.mapFromScene(snapped_scene)
                # Determine current tail (tip) scene position and convert to local
                tail_scene = pin.get_tip_scene_pos()
                tail_local = self.mapFromScene(tail_scene)
                # Update pin geometry to snapped head and preserved tail
                pin.set_visual_geometry(new_local.x(), new_local.y(), tail_local.x(), tail_local.y())
            except Exception:
                pass

class ElbowHandle(QGraphicsEllipseItem):
    def __init__(self, wire_item, index):
        super().__init__(-6, -6, 12, 12)
        self.wire_item = wire_item
        self.index = index
        self.setBrush(QBrush(ELBOW_COLOR))
        self.setPen(Qt.NoPen)
        # Tag this item so diagnostics can identify elbow handles vs other ellipse items
        try:
            self.setData(0, "elbow_handle")
        except Exception:
            pass
        # Keep size fixed on zoom; still accept drags so we can drive model updates.
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        # Do not let Qt move this item automatically; drives moves via model updates to avoid oscillation.
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(1003)

    def mouseMoveEvent(self, event):
        pos = event.scenePos()
        self.wire_item.move_elbow(self.index, pos)
        event.accept()

    def itemChange(self, change, value):
        # Prevent Qt from relocating the handle; position is owned by the model.
        if change == QGraphicsItem.ItemPositionChange:
            return self.pos()
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        self.wire_item.delete_elbow(self.index)
        event.accept()


class SegmentHandle(QGraphicsRectItem):
    def __init__(self, wire_item, segment_index, p1, p2):
        super().__init__(-5, -5, 10, 10)
        self.wire_item = wire_item
        self.segment_index = segment_index
        self.setBrush(QBrush(SEGMENT_HANDLE_COLOR))
        self.setPen(QPen(Qt.NoPen))
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        # Do not let Qt move this item automatically; drives moves via model updates to avoid oscillation.
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(1002)
        self._anchor_mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        # Snapshot of route at press time to prevent cumulative updates
        self._press_route_snapshot = None

    def mousePressEvent(self, event):
        # Capture anchor and snapshot on press so moves are computed relative to press state
        if self.wire_item:
            try:
                nodes = self.wire_item._build_nodes()
            except AttributeError:
                try:
                    nodes = self.wire_item._poly_points()
                except Exception:
                    nodes = []
            if self.segment_index < len(nodes) - 1:
                p1, p2 = nodes[self.segment_index], nodes[self.segment_index + 1]
                mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
                # Snap anchor to grid to ensure press-time baseline aligns with snapped moves
                self._anchor_mid = QPointF(round(mid.x() / GRID_SIZE) * GRID_SIZE, round(mid.y() / GRID_SIZE) * GRID_SIZE)
        # Capture route snapshot
        if hasattr(self.wire_item, 'route'):
            self._press_route_snapshot = list(self.wire_item.route)
        else:
            self._press_route_snapshot = list(getattr(self.wire_item.model, 'route', []))
        if HANDLE_DEBUG_VERBOSE:
            print(f"VERBOSE SegmentHandle.mousePressEvent: seg={self.segment_index} anchor_mid={self._anchor_mid} press_route={self._press_route_snapshot}")
        super().mousePressEvent(event)
        # Grab mouse so subsequent mouseMoveEvent calls are delivered to this handle
        try:
            self.grabMouse()
            event.accept()
        except Exception:
            pass

    def mouseMoveEvent(self, event):
        new_mid = event.scenePos()
        # Compute snapped cursor first and set the visual handle position immediately so it tracks the mouse
        snapped_cursor = QPointF(round(new_mid.x() / GRID_SIZE) * GRID_SIZE, round(new_mid.y() / GRID_SIZE) * GRID_SIZE)
        try:
            # Map the snapped scene point to the parent item's coordinates for correctness
            parent = self.parentItem() or self.wire_item
            mapped = parent.mapFromScene(snapped_cursor)
            if HANDLE_DEBUG_VERBOSE:
                print(f"VERBOSE SegmentHandle.mouseMoveEvent: seg={self.segment_index} snapped_cursor={snapped_cursor} mapped={mapped} before_pos={self.pos()}")
            self.setPos(mapped)
            if HANDLE_DEBUG_VERBOSE:
                print(f"VERBOSE SegmentHandle.mouseMoveEvent: after_setpos scene={self.mapToScene(self.boundingRect().center())} local={self.pos()}")
        except Exception:
            pass
        # Now update the model using the press snapshot so route changes from a stable baseline
        # Use snapped cursor as the new midpoint to keep model moves consistent with visual snaps
        self.wire_item.move_segment_handle(self.segment_index, snapped_cursor, self._anchor_mid, original_route=self._press_route_snapshot)
        # Also ensure handle is placed at the computed midpoint after model update
        try:
            nodes = self.wire_item._build_nodes()
        except AttributeError:
            try:
                nodes = self.wire_item._poly_points()
            except Exception:
                nodes = []
        if 0 <= self.segment_index < len(nodes) - 1:
            p1, p2 = nodes[self.segment_index], nodes[self.segment_index + 1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            try:
                parent = self.parentItem() or self.wire_item
                self.setPos(parent.mapFromScene(mid))
            except Exception:
                try:
                    self.setPos(mid)
                except Exception:
                    pass
            if HANDLE_DEBUG:
                print(f"DEBUG SegmentHandle.mouseMoveEvent: seg={self.segment_index} mid_scene={mid} handle_scene={self.mapToScene(self.boundingRect().center())}")
        event.accept()

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        # refresh anchor after a completed drag
        if self.wire_item:
            # WireItem implements _build_nodes(); TwistedBundleItem uses _poly_points
            try:
                nodes = self.wire_item._build_nodes()
            except AttributeError:
                try:
                    nodes = self.wire_item._poly_points()
                except Exception:
                    nodes = []
            if self.segment_index < len(nodes) - 1:
                p1, p2 = nodes[self.segment_index], nodes[self.segment_index + 1]
                self._anchor_mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        # Release mouse grab and clear snapshot
        try:
            self.ungrabMouse()
        except Exception:
            pass
        self._press_route_snapshot = None
        super().mouseReleaseEvent(event)


class WireLabelItem(QGraphicsItem):
    """Small label rendered near a point on the wire path.  Labels are draggable along the wire
    and update their underlying model.t_pos as they move.
    """
    def __init__(self, label_model, parent_wire_item):
        super().__init__(parent_wire_item)
        self.model = label_model
        self.wire_item = parent_wire_item
        self._font = QFont()
        self._font.setPointSize(10)
        self._padding = 4
        # Allow hover and left-button interaction; selection handled by parent if desired
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setZValue(2)
        try:
            self.setData(0, 'wire_label')
        except Exception:
            pass
        # Drag state
        self._dragging = False

    def boundingRect(self):
        fm = QFontMetricsF(self._font)
        # Qt5 used width(); Qt6 QFontMetricsF provides horizontalAdvance()
        try:
            text_w = fm.horizontalAdvance(self.model.text)
        except Exception:
            try:
                text_w = fm.width(self.model.text)
            except Exception:
                text_w = fm.boundingRect(self.model.text).width()
        w = text_w + (self._padding * 2)
        h = fm.height() + (self._padding * 2)
        return QRectF(-w/2, -h/2, w, h)

    def paint(self, painter, option, widget=None):
        br = self.boundingRect()
        # background
        painter.setBrush(QBrush(QColor(40, 40, 40, 230)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(br, 4, 4)
        # text
        painter.setPen(QPen(TEXT_COLOR))
        painter.setFont(self._font)
        painter.drawText(br, Qt.AlignCenter, self.model.text)

    # --- Interaction: drag along the wire ---
    def hoverEnterEvent(self, event):
        try:
            self.setCursor(Qt.OpenHandCursor)
        except Exception:
            pass
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        try:
            self.unsetCursor()
        except Exception:
            pass
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            try:
                self._dragging = True
                self.grabMouse()
                self.setCursor(Qt.ClosedHandCursor)
            except Exception:
                pass
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not getattr(self, '_dragging', False):
            event.ignore()
            return
        try:
            # Prefer parent's helper if present
            parent = self.wire_item
            if hasattr(parent, 'calculate_snap_to_polyline'):
                t, proj, seg = parent.calculate_snap_to_polyline(event.scenePos())
            else:
                # Fallback: compute projection using parent's polyline
                pts = parent._poly_points()
                if not pts:
                    t, proj, seg = 0.0, event.scenePos(), -1
                else:
                    # replicate projection logic from WireItem.calculate_snap_to_polyline
                    seg_lengths = []
                    total = 0.0
                    for i in range(len(pts) - 1):
                        seg_len = QLineF(pts[i], pts[i + 1]).length()
                        seg_lengths.append(seg_len)
                        total += seg_len
                    if total == 0:
                        t, proj, seg = 0.0, pts[0], -1
                    else:
                        best = None
                        acc = 0.0
                        for i in range(len(pts) - 1):
                            a, b = pts[i], pts[i + 1]
                            abx = b.x() - a.x()
                            aby = b.y() - a.y()
                            ab2 = abx * abx + aby * aby
                            if ab2 == 0:
                                proj = a
                                local_t = 0.0
                            else:
                                apx = event.scenePos().x() - a.x()
                                apy = event.scenePos().y() - a.y()
                                local_t = (apx * abx + apy * aby) / ab2
                                local_t = max(0.0, min(1.0, local_t))
                                proj = QPointF(a.x() + abx * local_t, a.y() + aby * local_t)
                            dx = event.scenePos().x() - proj.x()
                            dy = event.scenePos().y() - proj.y()
                            dist2 = dx * dx + dy * dy
                            if best is None or dist2 < best[0]:
                                seg_len = seg_lengths[i]
                                tval = (acc + (local_t * seg_len)) / total
                                best = (dist2, tval, proj, i)
                            acc += seg_lengths[i]
                        if best is None:
                            t, proj, seg = 0.0, pts[0], -1
                        else:
                            t, proj, seg = best[1], best[2], best[3]
            # Update model and visual position
            t = max(0.0, min(1.0, float(t)))
            self.model.t_pos = t
            self.setPos(self.wire_item.mapFromScene(proj))
            try:
                self.wire_item._notify_changed()
            except Exception:
                pass
            event.accept()
        except Exception:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if getattr(self, '_dragging', False):
            self._dragging = False
            try:
                self.ungrabMouse()
                self.unsetCursor()
            except Exception:
                pass
            # Finalize at release location
            try:
                parent = self.wire_item
                if hasattr(parent, 'calculate_snap_to_polyline'):
                    t, proj, seg = parent.calculate_snap_to_polyline(event.scenePos())
                else:
                    # re-run fallback projection (same as above)
                    pts = parent._poly_points() if hasattr(parent, '_poly_points') else []
                    if not pts:
                        t, proj, seg = 0.0, event.scenePos(), -1
                    else:
                        seg_lengths = []
                        total = 0.0
                        for i in range(len(pts) - 1):
                            seg_len = QLineF(pts[i], pts[i + 1]).length()
                            seg_lengths.append(seg_len)
                            total += seg_len
                        best = None
                        acc = 0.0
                        for i in range(len(pts) - 1):
                            a, b = pts[i], pts[i + 1]
                            abx = b.x() - a.x()
                            aby = b.y() - a.y()
                            ab2 = abx * abx + aby * aby
                            if ab2 == 0:
                                proj = a
                                local_t = 0.0
                            else:
                                apx = event.scenePos().x() - a.x()
                                apy = event.scenePos().y() - a.y()
                                local_t = (apx * abx + apy * aby) / ab2
                                local_t = max(0.0, min(1.0, local_t))
                                proj = QPointF(a.x() + abx * local_t, a.y() + aby * local_t)
                            dx = event.scenePos().x() - proj.x()
                            dy = event.scenePos().y() - proj.y()
                            dist2 = dx * dx + dy * dy
                            if best is None or dist2 < best[0]:
                                seg_len = seg_lengths[i]
                                tval = (acc + (local_t * seg_len)) / total
                                best = (dist2, tval, proj, i)
                            acc += seg_lengths[i]
                        if best is None:
                            t, proj, seg = 0.0, pts[0], -1
                        else:
                            t, proj, seg = best[1], best[2], best[3]
                t = max(0.0, min(1.0, float(t)))
                self.model.t_pos = t
                self.setPos(self.wire_item.mapFromScene(proj))
                try:
                    self.wire_item._notify_changed()
                except Exception:
                    pass
            except Exception:
                pass
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class WireItem(QGraphicsPathItem):
    def __init__(self, wire_model, source_item=None, target_item=None, on_changed=None, on_delete=None):
        super().__init__()
        self.model = wire_model
        self.source_dev = source_item
        self.target_dev = target_item
        self.src_pin_id = self.model.from_conn.split('.')[1]
        self.tgt_pin_id = self.model.to_conn.split('.')[1]
        self.on_changed = on_changed
        self.on_delete = on_delete

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)

        self.halo_path = QGraphicsPathItem(self)
        self.halo_path.setPen(QPen(SELECTED_COLOR, 6))
        self.halo_path.setOpacity(0.5)
        self.halo_path.hide()
        self.halo_path.setZValue(-1)

        self.segment_handles = []
        self.elbow_handles = []
        self.label_items = []
        self.src_pin_id = self.model.from_conn.split('.')[1]
        self.tgt_pin_id = self.model.to_conn.split('.')[1]
        self.on_changed = on_changed
        self.on_delete = on_delete

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)

        self.halo_path = QGraphicsPathItem(self)
        self.halo_path.setPen(QPen(SELECTED_COLOR, 6))
        self.halo_path.setOpacity(0.5)
        self.halo_path.hide()
        self.halo_path.setZValue(-1)

        self.segment_handles = []
        self.elbow_handles = []

        # Register wires with devices or twist nodes appropriately. DeviceItem expects a list
        # of attached_wires, while TwistNodeItem exposes register_wire(pin_id, wire_item).
        if self.source_dev:
            if hasattr(self.source_dev, "register_wire"):
                self.source_dev.register_wire(self.src_pin_id, self)
            else:
                self.source_dev.attached_wires.append(self)
        if self.target_dev:
            if hasattr(self.target_dev, "register_wire"):
                self.target_dev.register_wire(self.tgt_pin_id, self)
            else:
                self.target_dev.attached_wires.append(self)

        self.update_visuals()
        self.update_geometry()
        self.refresh_metadata()
        # Initialize label items from model
        try:
            for lbl in getattr(self.model, 'labels', []):
                try:
                    self.add_label_model(lbl)
                except Exception:
                    pass
        except Exception:
            pass

    def add_label_model(self, label_model):
        """Attach a WireLabel model and create its visual representation.
        Also persist the model into the wire model's labels list so it survives saves.
        """
        try:
            if not hasattr(self, 'label_items'):
                self.label_items = []
            # Ensure model persistence
            if not hasattr(self.model, 'labels'):
                self.model.labels = []
            if label_model not in self.model.labels:
                self.model.labels.append(label_model)
            itm = WireLabelItem(label_model, self)
            self.label_items.append(itm)
            # position now using build nodes
            try:
                pts = self._build_nodes()
                seg_lengths, total_len = self._segment_lengths(pts)
                pt, dir_vec = self._point_at(pts, seg_lengths, total_len, label_model.t_pos)
                itm.setPos(self.mapFromScene(pt))
            except Exception:
                pass
            return itm
        except Exception:
            pass

    def contextMenuEvent(self, event):
        menu = QMenu()
        twist_action = QAction("Twisted Pair", menu)
        entries = [("wire.delete", "Delete Wire", self._delete_wire_confirm)]

        color_menu = menu.addMenu("Change Color (DIN 47100)")
        palette = [
            ("WH", "White", "Neutral/control"),
            ("BN", "Brown", "Earth/ground"),
            ("RD", "Red", "Battery feed"),
            ("OG", "Orange", "Lighting feed"),
            ("YE", "Yellow", "Switched/accessory"),
            ("GN", "Green", "Sensor/signal"),
            ("BU", "Blue", "Data/comm"),
            ("VI", "Violet", "Diagnostics"),
            ("GY", "Gray", "Return/shield"),
            ("PK", "Pink", "Spare/aux"),
        ]
        for code, label, desc in palette:
            key = f"wire.color.{code}"
            def _set_color(c=code):
                self.set_color_code(c)
            color_menu.addAction(_make_action(color_menu, f"{code} — {desc}", _set_color, key))

        color_menu.addSeparator()
        pick_key = "wire.color.pick"
        color_menu.addAction(_make_action(color_menu, "Pick Color...", self._pick_custom_color, pick_key))

        for key, text, slot in sorted(entries, key=lambda e: (-_usage_rank(e[0]), entries.index(e))):
            menu.addAction(_make_action(menu, text, slot, key))
        menu.exec(event.screenPos())

    def _delete_wire_confirm(self):
        if not self.on_delete:
            return
        label = f"{self.model.from_conn} -> {self.model.to_conn}"
        resp = QMessageBox.question(
            None,
            "Delete Wire",
            f"Delete wire {label}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.on_delete(self)

    def _pick_custom_color(self):
        chosen = QColorDialog.getColor()
        if not chosen.isValid():
            return
        # Store hex string for custom colors
        self.set_color_code(chosen.name().upper())

    def set_color_code(self, code: str):
        if not code:
            return
        self.model.color = code
        self.update_visuals()
        self._update_tooltip()
        self._notify_changed()
        # If this wire is attached to any twist node, ensure the bundle visuals update to reflect color changes.
        if self.source_dev and hasattr(self.source_dev, 'bundle_refs'):
            for b in self.source_dev.bundle_refs:
                if b:
                    b.update_geometry()
        if self.target_dev and hasattr(self.target_dev, 'bundle_refs'):
            for b in self.target_dev.bundle_refs:
                if b:
                    b.update_geometry()

    def update_visuals(self):
        # DIN 47100-inspired palette
        color_map = {
            'WH': QColor(255, 255, 255),
            'BN': QColor(165, 42, 42),
            'RD': QColor(255, 0, 0),
            'OG': QColor(255, 165, 0),
            'YE': QColor(255, 255, 0),
            'GN': QColor(0, 255, 0),
            'BU': QColor(0, 0, 255),
            'VI': QColor(128, 0, 128),
            'GY': QColor(128, 128, 128),
            'PK': QColor(255, 192, 203),
            # Legacy
            'BK': QColor(0, 0, 0),
            'BL': QColor(0, 0, 255),
            'YL': QColor(255, 255, 0),
        }
        code = self.model.color
        if isinstance(code, str) and code.startswith('#'):
            base_color = QColor(code)
        else:
            base_color = color_map.get(code, QColor(150, 150, 150))
        self.setPen(QPen(base_color, WIRE_THICKNESS))
        self.halo_path.setPen(QPen(SELECTED_COLOR, 6))

    def refresh_metadata(self):
        # Devices (DeviceItem) have .model.meta; TwistNodeItem may be visual-only and lack .model.
        start_meta = getattr(getattr(self.source_dev, "model", None), "meta", {}) if self.source_dev else {}
        end_meta = getattr(getattr(self.target_dev, "model", None), "meta", {}) if self.target_dev else {}
        src_pin = self.source_dev.pins.get(self.src_pin_id) if (self.source_dev and hasattr(self.source_dev, "pins")) else None
        tgt_pin = self.target_dev.pins.get(self.tgt_pin_id) if (self.target_dev and hasattr(self.target_dev, "pins")) else None
        src_meta = getattr(getattr(src_pin, "model", None), "meta", {}) if src_pin else {}
        tgt_meta = getattr(getattr(tgt_pin, "model", None), "meta", {}) if tgt_pin else {}

        # Preserve existing custom meta, then overlay device/pin meta (end pin wins conflicts)
        merged = {**(self.model.meta or {}), **start_meta, **end_meta, **src_meta, **tgt_meta}
        self.model.meta = merged
        self._update_tooltip()

    def _update_tooltip(self):
        def fmt_endpoint(dev, pin_id):
            if not dev:
                return "?"
            # If the endpoint is backed by a device model, use its label/id; otherwise fall back to the visual item type.
            if hasattr(dev, 'model') and getattr(dev, 'model') is not None:
                dev_label = dev.model.label or dev.model.id
                pin = dev.pins.get(pin_id)
                pin_label = pin.model.label if pin and pin.model.label else pin_id
                return f"{html.escape(dev_label)} ({html.escape(dev.model.id)}) / {html.escape(pin_label)} ({html.escape(pin_id)})"
            else:
                typ = dev.__class__.__name__
                pin = dev.pins.get(pin_id)
                pin_label = pin.model.label if pin and getattr(pin, 'model', None) and pin.model.label else pin_id
                return f"{html.escape(typ)} / {html.escape(pin_label)} ({html.escape(pin_id)})"

        meta_text = json.dumps(self.model.meta or {}, sort_keys=True, indent=2)
        twist_line = "<tr><td style='padding-bottom:6px; background:#303030; border:0;'><b>Twisted:</b> Yes" + (f" (Pair {html.escape(self.model.pair_id)})" if self.model.pair_id else "") + "</td></tr>" if self.model.twisted else ""
        tip = (
            "<html><body style='margin:0; padding:0;' bgcolor='#303030'>"
            "<table cellpadding='10' cellspacing='0' bgcolor='#303030' "
            "style='color:#f5f5f5; font-family:monospace; font-size:11px; border:1px solid #272727; border-collapse:collapse; border-spacing:0;'>"
            f"<tr><td style='padding-bottom:4px; background:#303030; border:0;'><b>From:</b> {fmt_endpoint(self.source_dev, self.src_pin_id)}</td></tr>"
            f"<tr><td style='padding-bottom:6px; background:#303030; border:0;'><b>To:</b> {fmt_endpoint(self.target_dev, self.tgt_pin_id)}</td></tr>"
            f"{twist_line}"
            f"<tr><td style='background:#303030; border:0;'><b>Meta:</b><pre style='margin:6px 0 0 0; color:#f5f5f5; background:#252525; padding:8px; border:1px solid #272727;'>{html.escape(meta_text)}</pre></td></tr>"
            "</table></body></html>"
        )
        self.setToolTip(tip)

    def shape(self):
        # Broaden hit area to make elbow insertion clicks easier.
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(self.path())

    def _snap_point(self, pt: QPointF) -> QPointF:
        return QPointF(round(pt.x() / GRID_SIZE) * GRID_SIZE, round(pt.y() / GRID_SIZE) * GRID_SIZE)

    def _build_nodes(self):
        src_pin = self.source_dev.pins.get(self.src_pin_id) if self.source_dev else None
        tgt_pin = self.target_dev.pins.get(self.tgt_pin_id) if self.target_dev else None
        if not src_pin or not tgt_pin:
            return []
        nodes = [src_pin.get_tip_scene_pos()]
        nodes.extend([QPointF(x, y) for x, y in self.model.route])
        nodes.append(tgt_pin.get_tip_scene_pos())
        return nodes

    def _segment_insert_index(self, pt: QPointF, nodes):
        """Return index where an elbow should be inserted for point pt projected onto nodes polyline."""
        best_idx = 0
        best_dist = float('inf')
        for i in range(len(nodes) - 1):
            a = nodes[i]
            b = nodes[i+1]
            ab = b - a
            denom = ab.x() * ab.x() + ab.y() * ab.y()
            t = 0.0 if denom == 0 else ((pt - a).x() * ab.x() + (pt - a).y() * ab.y()) / denom
            t = max(0.0, min(1.0, t))
            proj = QPointF(a.x() + ab.x() * t, a.y() + ab.y() * t)
            dist = QLineF(pt, proj).length()
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return best_idx
    def update_geometry(self, rebuild_handles: bool = True):
        nodes = self._build_nodes()
        if len(nodes) < 2:
            return

        path = QPainterPath(nodes[0])
        for pt in nodes[1:]:
            path.lineTo(pt)
        self.setPath(path)
        if getattr(self, 'halo_path', None) is not None:
            self.halo_path.setPath(path)

        # Update label positions based on the current polyline geometry
        try:
            # Compute segment lengths and total length
            seg_lengths = []
            total_len = 0.0
            for i in range(len(nodes) - 1):
                seg_len = QLineF(nodes[i], nodes[i + 1]).length()
                seg_lengths.append(seg_len)
                total_len += seg_len
            # update labels if any
            try:
                self._update_labels_positions(nodes, seg_lengths, total_len)
            except Exception:
                pass
        except Exception:
            pass

        if rebuild_handles:
            self._rebuild_handles(nodes)
        else:
            self._update_handle_positions(nodes)

    def _rebuild_handles(self, nodes):
        # clear old
        for h in self.elbow_handles + self.segment_handles:
            if h.scene():
                h.scene().removeItem(h)
        self.elbow_handles = []
        self.segment_handles = []

        # elbows
        for idx, (x, y) in enumerate(self.model.route):
            handle = ElbowHandle(self, idx)
            handle.setParentItem(self)
            try:
                # route points are in scene coords; map to parent local coordinates
                handle.setPos(self.mapFromScene(QPointF(x, y)))
            except Exception:
                handle.setPos(x, y)
            self.elbow_handles.append(handle)

        # segments
        for i in range(len(nodes) - 1):
            p1, p2 = nodes[i], nodes[i+1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            handle = SegmentHandle(self, i, p1, p2)
            handle.setParentItem(self)
            try:
                handle.setPos(self.mapFromScene(mid))
            except Exception:
                handle.setPos(mid)
            self.segment_handles.append(handle)

    def _update_labels_positions(self, pts, seg_lengths, total_len):
        # Ensure label_items exist and stay aligned to self.model.labels
        try:
            if not hasattr(self, 'label_items'):
                self.label_items = []
            while len(self.label_items) > len(getattr(self.model, 'labels', [])):
                it = self.label_items.pop()
                try:
                    if it.scene():
                        it.scene().removeItem(it)
                except Exception:
                    pass
            for idx, lbl in enumerate(getattr(self.model, 'labels', [])):
                if idx >= len(self.label_items):
                    itm = WireLabelItem(lbl, self)
                    self.label_items.append(itm)
                else:
                    itm = self.label_items[idx]
                    itm.model = lbl
                try:
                    pt, dir_vec = self._point_at(pts, seg_lengths, total_len, lbl.t_pos)
                    itm.setPos(self.mapFromScene(pt))
                except Exception:
                    pass
        except Exception:
            pass
    def _update_handle_positions(self, nodes):
        # Update existing handles after a drag without recreating/removing the one under the cursor.
        for idx, handle in enumerate(self.elbow_handles):
            if idx < len(self.model.route):
                x, y = self.model.route[idx]
                try:
                    handle.setPos(self.mapFromScene(QPointF(x, y)))
                except Exception:
                    handle.setPos(x, y)
                if HANDLE_DEBUG:
                    scene_pos = handle.mapToScene(handle.boundingRect().center())
                    print(f"DEBUG Wire._update_handle_positions: elbow idx={idx} route=({x},{y}) handle_scene={scene_pos} handle_local={handle.pos()}")
                # Correction watchdog: if handle diverged from route, snap it to exact model position
                try:
                    scene_pos = handle.mapToScene(handle.boundingRect().center())
                    route_scene = QPointF(x, y)
                    dx = scene_pos.x() - route_scene.x()
                    dy = scene_pos.y() - route_scene.y()
                    if (dx*dx + dy*dy) ** 0.5 > 1.0:
                        handle.setPos(self.mapFromScene(route_scene))
                        handle.update()
                        try:
                            sc = self.scene()
                            if sc:
                                sc.update()
                                for v in sc.views():
                                    try:
                                        v.viewport().repaint()
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        if HANDLE_DEBUG or HANDLE_DEBUG_VERBOSE:
                            print(f"WATCHDOG: corrected elbow idx={idx} from {scene_pos} to {route_scene}")
                except Exception:
                    pass
                if HANDLE_DEBUG:
                    print(f"DEBUG Bundle._rebuild_elbow_handles: set elbow idx={idx} pos_scene=({x},{y}) pos_local={handle.pos()}")
                if HANDLE_DEBUG:
                    print(f"DEBUG Wire._rebuild_handles: set elbow idx={idx} pos_scene=({x},{y}) pos_local={handle.pos()}")

        if len(self.segment_handles) != len(nodes) - 1:
            # topology changed; rebuild fully
            self._rebuild_handles(nodes)
            return

        for i, handle in enumerate(self.segment_handles):
            p1, p2 = nodes[i], nodes[i+1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            try:
                handle.setPos(self.mapFromScene(mid))
            except Exception:
                handle.setPos(mid)

    def _segment_lengths(self, pts):
        lengths = []
        total = 0.0
        for i in range(len(pts) - 1):
            seg_len = QLineF(pts[i], pts[i + 1]).length()
            lengths.append(seg_len)
            total += seg_len
        return lengths, total

    def _point_at(self, pts, seg_lengths, total_len, t):
        if total_len == 0:
            return pts[0], QPointF(0, -1)
        target_dist = t * total_len
        acc = 0.0
        for i, seg_len in enumerate(seg_lengths):
            if seg_len == 0:
                continue
            if acc + seg_len >= target_dist:
                local_t = (target_dist - acc) / seg_len
                a, b = pts[i], pts[i + 1]
                x = a.x() + (b.x() - a.x()) * local_t
                y = a.y() + (b.y() - a.y()) * local_t
                dir_vec = QPointF(b.x() - a.x(), b.y() - a.y())
                return QPointF(x, y), dir_vec
            acc += seg_len
        return pts[-1], QPointF(0, -1)

    def calculate_snap_to_polyline(self, scene_point: QPointF):
        """Project a scene point onto this wire's polyline and return (t, proj_point, seg_idx).

        - t: normalized position along total path (0..1)
        - proj_point: QPointF in scene coordinates (projected point on polyline)
        - seg_idx: index of segment containing projection (0..n-2) or -1 if degenerate
        """
        nodes = self._build_nodes()
        if len(nodes) == 0:
            return 0.0, scene_point, -1
        if len(nodes) == 1:
            return 0.0, nodes[0], -1

        # Precompute segment lengths and total
        seg_lengths = []
        total = 0.0
        for i in range(len(nodes) - 1):
            seg_len = QLineF(nodes[i], nodes[i + 1]).length()
            seg_lengths.append(seg_len)
            total += seg_len

        if total == 0:
            return 0.0, nodes[0], -1

        best = None
        acc = 0.0
        for i in range(len(nodes) - 1):
            a = nodes[i]
            b = nodes[i + 1]
            abx = b.x() - a.x()
            aby = b.y() - a.y()
            ab2 = abx * abx + aby * aby
            if ab2 == 0:
                proj = a
                local_t = 0.0
            else:
                apx = scene_point.x() - a.x()
                apy = scene_point.y() - a.y()
                local_t = (apx * abx + apy * aby) / ab2
                if local_t < 0:
                    local_t = 0.0
                elif local_t > 1:
                    local_t = 1.0
                proj = QPointF(a.x() + abx * local_t, a.y() + aby * local_t)
            dx = scene_point.x() - proj.x()
            dy = scene_point.y() - proj.y()
            dist2 = dx * dx + dy * dy
            if best is None or dist2 < best[0]:
                seg_len = seg_lengths[i]
                t = (acc + (local_t * seg_len)) / total
                best = (dist2, t, proj, i)
            acc += seg_lengths[i]

        if best is None:
            return 0.0, nodes[0], -1
        return best[1], best[2], best[3]

    def _segment_normal(self, a: QPointF, b: QPointF) -> QPointF:
        dx = b.x() - a.x()
        dy = b.y() - a.y()
        if dx == 0 and dy == 0:
            return QPointF(0, 0)
        n = QPointF(-dy, dx)
        length = math.hypot(n.x(), n.y())
        if length == 0:
            return QPointF(0, 0)
        return QPointF(n.x() / length, n.y() / length)

    def add_elbow_at(self, pt: QPointF):
        pt = self._snap_point(pt)
        nodes = self._build_nodes()
        if len(nodes) < 2:
            return
        seg_idx = self._segment_insert_index(pt, nodes)
        self.model.route.insert(seg_idx, (pt.x(), pt.y()))
        self.update_geometry(rebuild_handles=True)
        self._notify_changed()

    def move_elbow(self, index: int, pt: QPointF):
        if index < 0 or index >= len(self.model.route):
            return
        pt = self._snap_point(pt)
        self.model.route[index] = (pt.x(), pt.y())
        self.update_geometry(rebuild_handles=False)
        self._notify_changed()

    def delete_elbow(self, index: int):
        if index < 0 or index >= len(self.model.route):
            return
        self.model.route.pop(index)
        self.update_geometry(rebuild_handles=True)
        self._notify_changed()

    def move_segment_handle(self, segment_index: int, new_mid: QPointF, anchor_mid: QPointF, original_route: list | None = None):
        nodes = self._build_nodes()
        if segment_index < 0 or segment_index >= len(nodes) - 1:
            return
        new_mid = self._snap_point(new_mid)
        delta = new_mid - anchor_mid
        if delta.isNull():
            return
        start_is_pin = segment_index == 0
        end_is_pin = segment_index + 1 == len(nodes) - 1

        if original_route is not None and len(original_route) == len(self.model.route):
            # Compute new route positions based on the original snapshot + delta (press-time anchored)
            new_route = list(original_route)
            if not start_is_pin:
                ridx = segment_index - 1
                new_route[ridx] = (original_route[ridx][0] + delta.x(), original_route[ridx][1] + delta.y())
            if not end_is_pin:
                ridx = segment_index
                if ridx < len(new_route):
                    new_route[ridx] = (original_route[ridx][0] + delta.x(), original_route[ridx][1] + delta.y())
            self.model.route = new_route
        else:
            # Only move elbows (route points)
            if not start_is_pin:
                ridx = segment_index - 1
                self.model.route[ridx] = (self.model.route[ridx][0] + delta.x(), self.model.route[ridx][1] + delta.y())
            if not end_is_pin:
                ridx = segment_index
                if ridx < len(self.model.route):
                    self.model.route[ridx] = (self.model.route[ridx][0] + delta.x(), self.model.route[ridx][1] + delta.y())

        self.update_geometry(rebuild_handles=False)
        self._notify_changed()

    def mouseDoubleClickEvent(self, event):
        self.add_elbow_at(event.scenePos())
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.halo_path.setVisible(value)
        return super().itemChange(change, value)

    def _notify_changed(self):
        if callable(self.on_changed):
            self.on_changed()


class TwistNodeItem(QGraphicsItem):
    """Minimal junction for twisted-pair bundles.

    Layout: two pins on the left (High/Low), one on the right (Shield).
    Compact visual, no label.
    """

    WIDTH = 44
    HEIGHT = 26

    def __init__(self, label="Twist", on_changed=None):
        super().__init__()
        self.on_changed = on_changed
        self.attached_wires: dict[str, list] = defaultdict(list)
        self.bundle_refs: list = []

        self._rect = QRectF(0, 0, self.WIDTH, self.HEIGHT)
        self._brush = QBrush(QColor(55, 55, 65))
        self._pen = QPen(QColor(170, 200, 255), 1.8)

        # Removed rectangular halo; use the control pivot ellipse for selection highlight
        self.halo = None

        self.pins: dict[str, PinItem] = {}
        self._rotation = 0  # rotation state (0..3), clockwise 90deg steps
        self._build_pins()

        # Control pivot: visible ellipse representing control node center (10px dia)
        try:
            # Control pivot ellipse centered at the node pivot (size governed by CONTROL_PIVOT_DIAM)
            r = CONTROL_PIVOT_DIAM / 2.0
            self.control_pivot = QGraphicsEllipseItem(-r, -r, CONTROL_PIVOT_DIAM, CONTROL_PIVOT_DIAM, self)
            # Default: filled dark blue for unselected pivot (device-space fixed size)
            try:
                self.control_pivot.setBrush(QBrush(PIVOT_COLOR))
            except Exception:
                self.control_pivot.setBrush(Qt.NoBrush)
            self.control_pivot.setPen(Qt.NoPen)
            self.control_pivot.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
            # Keep the pivot non-interactive so the node's shape handles clicks
            try:
                self.control_pivot.setAcceptedMouseButtons(Qt.NoButton)
            except Exception:
                pass
            self.control_pivot.setZValue(3)
            try:
                self.control_pivot.setData(0, 'control_pivot')
            except Exception:
                pass
            # Position it using current pivot value
            try:
                self.control_pivot.setPos(self._pivot)
            except Exception:
                pass

            # Selection ring (hidden by default) to make the pivot selection unmistakable
            try:
                ring_r = r + SELECTED_RING_PAD
                ring_diam = ring_r * 2
                self.control_pivot_ring = QGraphicsEllipseItem(-ring_r, -ring_r, ring_diam, ring_diam, self)
                self.control_pivot_ring.setBrush(Qt.NoBrush)
                self.control_pivot_ring.setPen(QPen(SELECTED_COLOR, SELECTED_RING_WIDTH))
                self.control_pivot_ring.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
                self.control_pivot_ring.setZValue(4)
                self.control_pivot_ring.setVisible(False)
                try:
                    self.control_pivot_ring.setData(0, 'control_pivot_ring')
                except Exception:
                    pass
                try:
                    self.control_pivot_ring.setPos(self._pivot)
                except Exception:
                    pass
            except Exception:
                self.control_pivot_ring = None

            # Selection label (hidden by default)
            try:
                self.control_pivot_label = QGraphicsSimpleTextItem(SELECTED_LABEL_TEXT, self)
                f = QFont()
                f.setPointSize(10)
                f.setBold(True)
                self.control_pivot_label.setFont(f)
                # Make the label highly visible (white)
                try:
                    self.control_pivot_label.setBrush(QBrush(TEXT_COLOR))
                except Exception:
                    pass
                self.control_pivot_label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
                self.control_pivot_label.setZValue(5)
                self.control_pivot_label.setVisible(False)
                try:
                    br = self.control_pivot_label.boundingRect()
                    self.control_pivot_label.setPos(self._pivot + QPointF(ring_r + 4, -br.height() / 2))
                except Exception:
                    pass
            except Exception:
                self.control_pivot_label = None
            # Add a small always-visible dot (device-coordinate fixed) so the pivot remains visible
            # regardless of zoom level. This dot is independent of the hollow pivot outline used for
            # selection highlighting so tests that expect the pivot brush to be NoBrush still pass.
            try:
                # Small always-visible dot centered on pivot (size governed by CONTROL_DOT_DIAM)
                dr = CONTROL_DOT_DIAM / 2.0
                self.control_dot = QGraphicsEllipseItem(-dr, -dr, CONTROL_DOT_DIAM, CONTROL_DOT_DIAM, self)
                self.control_dot.setBrush(QBrush(QColor(180, 180, 180)))
                self.control_dot.setPen(Qt.NoPen)
                self.control_dot.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
                # Keep the small always-visible dot non-interactive so node shape receives clicks
                try:
                    self.control_dot.setAcceptedMouseButtons(Qt.NoButton)
                except Exception:
                    pass
                self.control_dot.setZValue(4)
                try:
                    self.control_dot.setData(0, 'control_dot')
                except Exception:
                    pass
                self.control_dot.setPos(self._pivot)
            except Exception:
                self.control_dot = None
        except Exception:
            self.control_pivot = None

        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self._drag_start_pos = None
        self._item_start_pos = None
        # Hover state for proximity highlighting
        self._pivot_hover = False
        # Track previous position so we can compute deltas when the node moves
        self._prev_pos = self.pos()
        # Pivot relocation state: allow user to explicitly relocate pivot via Shift+drag
        self._pivot_dragging = False
        self._pivot_locked = False
        self._pivot_drag_start_scene = None
        self._pivot_start_local = None

    def set_pivot_hover(self, hover: bool):
        """Set transient hover highlight for control pivot (non-selection visual)."""
        try:
            if getattr(self, 'control_pivot', None) is None:
                return
            # Do not override selection state
            if self.isSelected():
                self._pivot_hover = False
                return
            if hover:
                self._pivot_hover = True
                # Use a subtle highlight (semi-transparent fill)
                try:
                    self.control_pivot.setBrush(QBrush(QColor(255, 200, 50, 120)))
                    self.control_pivot.setPen(QPen(QColor(255, 200, 50), 1.6))
                except Exception:
                    pass
            else:
                self._pivot_hover = False
                try:
                    # Restore to default: filled blue for free nodes, hollow when bundle attached
                    if getattr(self, 'bundle_refs', None):
                        self.control_pivot.setBrush(Qt.NoBrush)
                    else:
                        self.control_pivot.setBrush(QBrush(ELBOW_COLOR))
                    self.control_pivot.setPen(Qt.NoPen)
                except Exception:
                    pass
            try:
                self.update()
            except Exception:
                pass
        except Exception:
            pass

    def itemChange(self, change, value):
        # Ensure pins align to the global grid once this node is added to a scene
        if change == QGraphicsItem.ItemSceneChange:
            if value:
                try:
                    self._enforce_pin_grid()
                except Exception:
                    pass


        if change == QGraphicsItem.ItemSelectedHasChanged:
            # Highlight control pivot ellipse when node is selected (no rectangular halos)
            try:
                if getattr(self, 'control_pivot', None):
                    if value:
                        # Deselect any attached bundles so selection is unambiguous
                        try:
                            for b in list(self.bundle_refs):
                                try:
                                    b.setSelected(False)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        self.control_pivot.setPen(QPen(QColor(120, 120, 120), 1.2))
                    self.update()
            except Exception:
                pass

        # Snap node position to the global GRID on moves so control nodes align to the grid
        if change == QGraphicsItem.ItemPositionChange and isinstance(value, QPointF):
            try:
                snapped = QPointF(round(value.x() / GRID_SIZE) * GRID_SIZE, round(value.y() / GRID_SIZE) * GRID_SIZE)
                return snapped
            except Exception:
                pass

        if change == QGraphicsItem.ItemPositionHasChanged:
            # Compute delta from previous position and update attached wires & bundles
            try:
                new_pos = value if isinstance(value, QPointF) else self.pos()
                # Enforce snapping for non-interactive moves (e.g., setPos calls)
                try:
                    snapped_pos = QPointF(round(new_pos.x() / GRID_SIZE) * GRID_SIZE, round(new_pos.y() / GRID_SIZE) * GRID_SIZE)
                    if snapped_pos != new_pos:
                        # Schedule a setPos after the current event loop to avoid re-entrancy and ensure
                        # the position change goes through the normal QGraphicsItem change cycle.
                        try:
                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(0, lambda sp=snapped_pos: self.setPos(sp))
                        except Exception:
                            try:
                                self.setPos(snapped_pos)
                            except Exception:
                                pass
                        return super().itemChange(change, value)
                except Exception:
                    pass
                delta = QPointF(new_pos.x() - self._prev_pos.x(), new_pos.y() - self._prev_pos.y())
                self._prev_pos = QPointF(new_pos)
            except Exception:
                delta = QPointF(0, 0)

            # Notify attached wires to refresh geometry
            for pwires in self.attached_wires.values():
                for w in pwires:
                    try:
                        w.update_geometry()
                    except Exception:
                        pass

            # Notify any attached bundles so they can translate implicit/explicit elbows
            for b in list(self.bundle_refs):
                try:
                    b.node_moved(self, delta)
                except Exception:
                    pass

            # Enforce pin grid alignment on node moves as well
            try:
                self._enforce_pin_grid()
            except Exception:
                pass

            if callable(self.on_changed):
                self.on_changed()

        return super().itemChange(change, value)

    def _build_pins(self):
        # Recreate pin visuals based on the current rotation state.
        for pin in list(self.pins.values()):
            try:
                if getattr(pin, 'leader', None) and pin.leader.scene():
                    pin.leader.scene().removeItem(pin.leader)
            except Exception:
                pass
            try:
                if pin.scene():
                    pin.scene().removeItem(pin)
            except Exception:
                pass
        self.pins = {}

        # Base (unrotated) geometry for pins
        high = PinModel(id="H", label="H", side=Side.LEFT)
        low = PinModel(id="L", label="L", side=Side.LEFT)
        shield = PinModel(id="S", label="S", side=Side.RIGHT)

        # Local positions in unrotated coordinates
        # Place H/L pins orthogonally with fixed spacing equal to 2 * GRID_SIZE (40px)
        # to position H/L around the control pivot. Pins will then
        # snap to the global GRID via _enforce_pin_grid.
        spacing = GRID_SIZE * 2
        half = spacing / 2.0
        cy = self.HEIGHT / 2.0
        cx = self.WIDTH / 2.0
        y_top = cy - half
        y_bottom = cy + half

        # Determine which side should hold the High/Low pins for external connections.
        # If a bundle is attached to one side, place H/L on the opposite side so users can
        # connect regular wires there. Shield pin is placed on the bundle side.
        bundle_side = getattr(self, '_bundle_side', None)
        def opp(side):
            return {
                Side.LEFT: Side.RIGHT,
                Side.RIGHT: Side.LEFT,
                Side.TOP: Side.BOTTOM,
                Side.BOTTOM: Side.TOP,
            }.get(side, Side.RIGHT)

        if bundle_side is None:
            hl_side = Side.LEFT
            shield_side = Side.RIGHT
        else:
            hl_side = opp(bundle_side)
            shield_side = bundle_side

        # Map side to coordinates
        def side_coords(side, x_offset):
            if side == Side.LEFT:
                return (0.0, x_offset, -6.0, x_offset)
            if side == Side.RIGHT:
                return (self.WIDTH, x_offset, self.WIDTH + 6.0, x_offset)
            if side == Side.TOP:
                return (self.WIDTH * 0.5 + x_offset, 0.0, self.WIDTH * 0.5 + x_offset, -6.0)
            # bottom
            return (self.WIDTH * 0.5 + x_offset, self.HEIGHT, self.WIDTH * 0.5 + x_offset, self.HEIGHT + 6.0)

        coords = {
            "H": (*side_coords(hl_side, y_top), hl_side, True),
            "L": (*side_coords(hl_side, y_bottom), hl_side, True),
            # Shield is on the bundle side and should be hidden visually
            "S": (*side_coords(shield_side, self.HEIGHT * 0.5), shield_side, False),
        }

        # Apply rotation (0..3) clockwise by 90 degrees increments around a pivot.
        # Pivot is offset slightly toward the bundle side (if present) so the edit grip
        # doesn't overlap connectors visually.
        cx = self.WIDTH / 2.0
        cy = self.HEIGHT / 2.0

        # Compute pivot positioned outside the node on the bundle side so it acts as
        # an edit grip and does not interfere with selecting the pins. The pivot is
        # placed a fixed distance beyond the node's edge toward the bundle (GRID_SIZE).
        bundle_side = shield_side
        # Use GRID_SIZE so pivot distance aligns with the standard snap grid (20px)
        outward = getattr(self, '_pivot_outward', GRID_SIZE)

        if bundle_side == Side.LEFT:
            pivot_x = -outward
            pivot_y = cy
        elif bundle_side == Side.RIGHT:
            pivot_x = self.WIDTH + outward
            pivot_y = cy
        elif bundle_side == Side.TOP:
            pivot_x = cx
            pivot_y = -outward
        else:  # bottom
            pivot_x = cx
            pivot_y = self.HEIGHT + outward

        # store pivot for use by paint and tests
        self._pivot = QPointF(pivot_x, pivot_y)

        def rotate_point(x, y, rot):
            # Translate to pivot
            rx = x - pivot_x
            ry = y - pivot_y
            if rot == 0:
                nx, ny = rx, ry
            elif rot == 1:
                nx, ny = ry, -rx
            elif rot == 2:
                nx, ny = -rx, -ry
            else:
                nx, ny = -ry, rx
            return nx + pivot_x, ny + pivot_y

        # Side rotation mapping clockwise
        side_order = [Side.LEFT, Side.TOP, Side.RIGHT, Side.BOTTOM]

        for pid, (x1, y1, x2, y2, base_side, show_flag) in coords.items():
            nx1, ny1 = rotate_point(x1, y1, getattr(self, '_rotation', 0))
            nx2, ny2 = rotate_point(x2, y2, getattr(self, '_rotation', 0))
            # Compute rotated side
            base_idx = side_order.index(base_side) if base_side in side_order else 0
            rotated_side = side_order[(base_idx + getattr(self, '_rotation', 0)) % 4]
            pm = PinModel(id=pid, label=pid, side=rotated_side)
            # Determine whether to show this pin visually after accounting for rotation
            show_after_rot = show_flag
            # If rotation rotates the bundle side into view, hide accordingly (simple approach assumes flag rotates too)
            self._add_pin(pm, x1=nx1, y1=ny1, x2=nx2, y2=ny2, show=show_after_rot)
        # After building pins, enforce grid lock so pin heads are positioned on the GRID
        try:
            self._enforce_pin_grid()
        except Exception:
            pass
        # Update pivot location so it sits exactly one GRID away from the pin head line
        try:
            self._update_pivot_from_pins()
            # Ensure leaders are refreshed after pins/pivot changes
            try:
                for pid, pin in list(self.pins.items()):
                    try:
                        pin.update_leader()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def _add_pin(self, pin_model: PinModel, x1, y1, x2, y2, show: bool = True):
        pin = PinItem(pin_model, self)
        pin.set_visual_geometry(x1, y1, x2, y2)
        # Show or hide the pin visuals (hidden pins still exist for bookkeeping but are not visible/interactive)
        if not show:
            pin.hide()
            pin.setAcceptHoverEvents(False)
            try:
                if pin.leader:
                    pin.leader.hide()
            except Exception:
                pass
        self.pins[pin_model.id] = pin

    def register_wire(self, pin_id: str, wire_item):
        self.attached_wires[pin_id].append(wire_item)

    def register_bundle(self, bundle_item):
        if bundle_item not in self.bundle_refs:
            self.bundle_refs.append(bundle_item)
        # When a bundle attaches, compute which side of this node the bundle sits on
        # using the vector toward the other node. Reserve that side so external wires
        # cannot connect to pins on the bundle side.
        if hasattr(bundle_item, 'source_node') and hasattr(bundle_item, 'target_node'):
            other = bundle_item.source_node if bundle_item.target_node is self else bundle_item.target_node
            vec = other.pos() - self.pos()
            # Decide side by largest component
            if abs(vec.x()) >= abs(vec.y()):
                self._bundle_side = Side.RIGHT if vec.x() > 0 else Side.LEFT
            else:
                self._bundle_side = Side.BOTTOM if vec.y() > 0 else Side.TOP
        # Rebuild pins so H/L appear on the non-bundle side (connectable)
        self._build_pins()
        # Ensure leaders are refreshed after pin rebuild
        try:
            for pid, pin in list(self.pins.items()):
                try:
                    pin.update_leader()
                except Exception:
                    pass
        except Exception:
            pass
        # Show pivot/marker on top of bundle; default unhighlighted
        self._pivot_highlight = False
        # Hide the filled control dot while a bundle is attached so pivot appears suppressed
        if getattr(self, 'control_dot', None):
            try:
                self.control_dot.setBrush(Qt.NoBrush)
            except Exception:
                pass
        # Keep the pivot filled dark-blue even when a bundle attaches; bundle selection will
        # indicate an outline in response to bundle selection, but the pivot remains visible.
        if callable(self.on_changed):
            self.on_changed()

    def unregister_wire(self, pin_id: str, wire_item):
        # backward compatibility; unused for bundles
        pass

    def unregister_bundle(self, bundle_item):
        if bundle_item in self.bundle_refs:
            self.bundle_refs.remove(bundle_item)
        # Clear _bundle_side if no bundles remain
        if not self.bundle_refs:
            self._bundle_side = None
        # Otherwise recompute side from remaining bundles (take first)
        elif self.bundle_refs:
            b = self.bundle_refs[0]
            other = b.source_node if b.target_node is self else b.target_node
            vec = other.pos() - self.pos()
            if abs(vec.x()) >= abs(vec.y()):
                self._bundle_side = Side.RIGHT if vec.x() > 0 else Side.LEFT
            else:
                self._bundle_side = Side.BOTTOM if vec.y() > 0 else Side.TOP
        # Rebuild pins to reflect changed reservation
        self._build_pins()
        # Reset pivot highlight
        self._pivot_highlight = False
        # Restore control_dot visibility when no bundles remain
        if not self.bundle_refs and getattr(self, 'control_dot', None):
            try:
                self.control_dot.setBrush(QBrush(QColor(180, 180, 180)))
            except Exception:
                pass
        # Restore pivot fill to blue (ELBOW_COLOR) when no bundles remain and node isn't selected
        if not self.bundle_refs and getattr(self, 'control_pivot', None):
            try:
                # If node is selected, selection color logic will override
                if not self.isSelected():
                    self.control_pivot.setBrush(QBrush(ELBOW_COLOR))
            except Exception:
                pass
        if callable(self.on_changed):
            self.on_changed()

    def pin_connectable(self, pin_id: str) -> bool:
        """Return True if a pin with given id is allowed to be connected by external wires.
        Pins on the node's reserved bundle side are not connectable.
        """
        pin = self.pins.get(pin_id)
        if not pin:
            return False
        if getattr(self, '_bundle_side', None) is None:
            return True
        return pin.model.side != getattr(self, '_bundle_side', None)

    def rotate_cw(self, steps: int = 1):
        """Rotate this node clockwise by 90deg * steps and rebuild pins.
        Skip any rotation that would point the H/L side at the bundle side (disallowed).
        """
        # Try up to 4 steps to find a valid rotation
        attempts = 0
        while attempts < 4:
            new_rot = (self._rotation + (steps % 4)) % 4
            # Determine resulting H/L side after rotation
            side_order = [Side.LEFT, Side.TOP, Side.RIGHT, Side.BOTTOM]
            # Current H/L is calculated in _build_pins based on _bundle_side; infer current HL before rotation
            # Simpler approach: compute base HL (when rotation=0 it is the computed HL), and simulate time to new_rot
            # To be conservative, check resulting rotated HL against bundle side
            # Temporarily set rotation and ask _build_pins to compute (without committing long-term change)
            old_rot = self._rotation
            self._rotation = new_rot
            # Recompute pins in-memory to inspect HL location
            # Use a shallow rebuild: call _build_pins and then read where H ended up
            self._build_pins()
            # Determine where H's side is now
            h_pin = self.pins.get('H')
            resulting_h_side = h_pin.model.side if h_pin else None
            # revert to previous rotation and pins (we will set again below as needed)
            self._rotation = old_rot
            self._build_pins()

            if getattr(self, '_bundle_side', None) is not None and resulting_h_side == self._bundle_side:
                # rotation would point H at bundle side; skip by advancing one more step
                steps = (steps + 1) % 4
                attempts += 1
                continue

            # Accept this rotation
            self._rotation = new_rot
            self._build_pins()
            for b in list(self.bundle_refs):
                if b:
                    b.update_geometry()
            if callable(self.on_changed):
                self.on_changed()
            return
        # If no safe rotation found, do nothing
        return

    def unregister_wire(self, pin_id: str, wire_item):
        if pin_id in self.attached_wires and wire_item in self.attached_wires[pin_id]:
            self.attached_wires[pin_id].remove(wire_item)

    def first_wire_color(self, pin_id: str):
        wires = self.attached_wires.get(pin_id) or []
        if not wires:
            return None
        pen = getattr(wires[0], "pen", None)
        return pen().color() if callable(pen) else None

    def get_pin_tip_scene_pos(self, pin_id: str):
        pin = self.pins.get(pin_id)
        if not pin:
            return self.mapToScene(self._rect.center())
        return pin.get_tip_scene_pos()

    def _enforce_pin_grid(self):
        """Snap pin head positions to the global GRID_SIZE so that pin tips remain grid-locked.
        This adjusts the pin local position and recomputes the leader line to preserve the tail anchor.

        Additionally, align pin head columns/rows so that the head lies exactly one GRID
        unit away from the node control pivot along the outward axis (LEFT/RIGHT/ TOP/BOTTOM).
        """
        for pid, pin in list(self.pins.items()):
            try:
                # Determine current pin head scene position and snap horizontally to GRID while preserving Y
                head_scene = pin.mapToScene(0, 0)
                snapped_x = round(head_scene.x() / GRID_SIZE) * GRID_SIZE
                snapped_scene = QPointF(snapped_x, head_scene.y())

                # If this node has a defined pivot/bundle side, enforce that the pin head
                # lies exactly one GRID unit away from the pivot along the outward axis.
                try:
                    side = getattr(self, '_bundle_side', None)
                    if not side and getattr(self, 'bundle_refs', None):
                        b = self.bundle_refs[0]
                        other = b.source_node if b.target_node is self else b.target_node
                        vec = other.pos() - self.pos()
                        if abs(vec.x()) >= abs(vec.y()):
                            side = Side.RIGHT if vec.x() > 0 else Side.LEFT
                        else:
                            side = Side.BOTTOM if vec.y() > 0 else Side.TOP
                except Exception:
                    side = getattr(self, '_bundle_side', None)

                try:
                    if hasattr(self, '_pivot') and side is not None:
                        pivot_scene = self.mapToScene(self._pivot)
                        # For LEFT/RIGHT nodes, enforce H above and L below the pivot by one GRID unit.
                        if side in (Side.LEFT, Side.RIGHT):
                            if side == Side.LEFT:
                                snapped_scene.setX(pivot_scene.x() + GRID_SIZE)
                            else:
                                snapped_scene.setX(pivot_scene.x() - GRID_SIZE)
                            # Enforce vertical offset for H / L pins
                            if pid == 'H':
                                snapped_scene.setY(pivot_scene.y() - GRID_SIZE)
                            elif pid == 'L':
                                snapped_scene.setY(pivot_scene.y() + GRID_SIZE)
                        else:
                            # For TOP/BOTTOM, preserve previous behavior (align along outward axis)
                            if side == Side.TOP:
                                snapped_scene.setY(pivot_scene.y() + GRID_SIZE)
                            elif side == Side.BOTTOM:
                                snapped_scene.setY(pivot_scene.y() - GRID_SIZE)
                except Exception:
                    pass

                # Map snapped scene point back to node-local coords
                new_local = self.mapFromScene(snapped_scene)
                # Determine current tail (tip) scene position and convert to local
                tail_scene = pin.get_tip_scene_pos()
                tail_local = self.mapFromScene(tail_scene)
                # Update pin geometry to snapped head and preserved tail
                pin.set_visual_geometry(new_local.x(), new_local.y(), tail_local.x(), tail_local.y())
            except Exception:
                pass

    def _update_pivot_from_pins(self):
        """Position the node pivot one GRID unit away from the line formed by its H/L pin heads.
        Uses scene coordinates for robust calculation and snaps pivot position to GRID lines."""
        # Respect explicit user pivot relocations: if pivot is locked by the user, do not auto-update
        if getattr(self, '_pivot_locked', False):
            return
        try:
            h_scene = self.get_pin_tip_scene_pos('H')
            l_scene = self.get_pin_tip_scene_pos('L')
            # midpoint between heads
            mid_y = (h_scene.y() + l_scene.y()) / 2.0
            # decide direction based on bundle side: compute from attached bundle vector if available
            side = getattr(self, '_bundle_side', None)
            try:
                if not side and getattr(self, 'bundle_refs', None):
                    b = self.bundle_refs[0]
                    other = b.source_node if b.target_node is self else b.target_node
                    vec = other.pos() - self.pos()
                    if abs(vec.x()) >= abs(vec.y()):
                        side = Side.RIGHT if vec.x() > 0 else Side.LEFT
                    else:
                        side = Side.BOTTOM if vec.y() > 0 else Side.TOP
            except Exception:
                pass
            if not side:
                side = Side.LEFT
            node_rect = self.sceneBoundingRect()
            if side == Side.LEFT:
                # Prefer node-local offset so x sits exactly at -GRID_SIZE
                pivot_local_x = -GRID_SIZE
                pivot_local_y = self.HEIGHT / 2.0
                self._pivot = QPointF(pivot_local_x, pivot_local_y)
                # Snap pivot's scene position to GRID so the control pivot lies on grid intersections
                try:
                    scene_pivot = self.mapToScene(self._pivot)
                    snapped_scene = QPointF(round(scene_pivot.x() / GRID_SIZE) * GRID_SIZE, round(scene_pivot.y() / GRID_SIZE) * GRID_SIZE)
                    self._pivot = self.mapFromScene(snapped_scene)
                except Exception:
                    pass
                try:
                    if getattr(self, 'control_pivot', None):
                        self.control_pivot.setPos(self._pivot)
                    if getattr(self, 'control_dot', None):
                        self.control_dot.setPos(self._pivot)
                except Exception:
                    pass
                # Update leaders
                for pid, pin in list(self.pins.items()):
                    try:
                        pin.update_leader()
                    except Exception:
                        pass
                return
            elif side == Side.RIGHT:
                pivot_local_x = self.WIDTH + GRID_SIZE
                pivot_local_y = self.HEIGHT / 2.0
                self._pivot = QPointF(pivot_local_x, pivot_local_y)
                # Snap pivot's scene position to GRID so the control pivot lies on grid intersections
                try:
                    scene_pivot = self.mapToScene(self._pivot)
                    snapped_scene = QPointF(round(scene_pivot.x() / GRID_SIZE) * GRID_SIZE, round(scene_pivot.y() / GRID_SIZE) * GRID_SIZE)
                    self._pivot = self.mapFromScene(snapped_scene)
                except Exception:
                    pass
                try:
                    if getattr(self, 'control_pivot', None):
                        self.control_pivot.setPos(self._pivot)
                except Exception:
                    pass
                for pid, pin in list(self.pins.items()):
                    try:
                        pin.update_leader()
                    except Exception:
                        pass
                return
            elif side == Side.TOP:
                pivot_y_scene = node_rect.top() - GRID_SIZE
                pivot_x_scene = (h_scene.x() + l_scene.x()) / 2.0
                snapped = QPointF(round(pivot_x_scene / GRID_SIZE) * GRID_SIZE, round(pivot_y_scene / GRID_SIZE) * GRID_SIZE)
                self._pivot = self.mapFromScene(snapped)
                # Ensure pivot scene position is snapped to GRID
                try:
                    scene_pivot = self.mapToScene(self._pivot)
                    snapped_scene = QPointF(round(scene_pivot.x() / GRID_SIZE) * GRID_SIZE, round(scene_pivot.y() / GRID_SIZE) * GRID_SIZE)
                    self._pivot = self.mapFromScene(snapped_scene)
                except Exception:
                    pass
                try:
                    if getattr(self, 'control_pivot', None):
                        self.control_pivot.setPos(self._pivot)
                except Exception:
                    pass
                for pid, pin in list(self.pins.items()):
                    try:
                        pin.update_leader()
                    except Exception:
                        pass
                return
            else:  # BOTTOM
                pivot_y_scene = node_rect.bottom() + GRID_SIZE
                pivot_x_scene = (h_scene.x() + l_scene.x()) / 2.0
                snapped = QPointF(round(pivot_x_scene / GRID_SIZE) * GRID_SIZE, round(pivot_y_scene / GRID_SIZE) * GRID_SIZE)
                self._pivot = self.mapFromScene(snapped)
                # Ensure pivot scene position is snapped to GRID
                try:
                    scene_pivot = self.mapToScene(self._pivot)
                    snapped_scene = QPointF(round(scene_pivot.x() / GRID_SIZE) * GRID_SIZE, round(scene_pivot.y() / GRID_SIZE) * GRID_SIZE)
                    self._pivot = self.mapFromScene(snapped_scene)
                except Exception:
                    pass
                try:
                    if getattr(self, 'control_pivot', None):
                        self.control_pivot.setPos(self._pivot)
                except Exception:
                    pass
                for pid, pin in list(self.pins.items()):
                    try:
                        pin.update_leader()
                    except Exception:
                        pass
                return
            # Snap: ensure pivot stays outside node by using floor/ceil accordingly
            if side == Side.LEFT:
                snapped_x = math.floor(pivot_x_scene / GRID_SIZE) * GRID_SIZE
            else:
                snapped_x = math.ceil(pivot_x_scene / GRID_SIZE) * GRID_SIZE
            snapped_y = round(pivot_y_scene / GRID_SIZE) * GRID_SIZE
            snapped = QPointF(snapped_x, snapped_y)
            # DEBUG: print values so we can inspect why pivot does not match expectation
            try:
                print(f"DEBUG _update_pivot_from_pins: pivot_x_scene={pivot_x_scene}, mid_y={mid_y}, snapped={snapped}, bundle_side={getattr(self,'_bundle_side',None)}")
            except Exception:
                pass
            self._pivot = self.mapFromScene(snapped)
            # Update control pivot visual position and leaders for pins
            try:
                if getattr(self, 'control_pivot', None):
                    try:
                        self.control_pivot.setPos(self._pivot)
                    except Exception:
                        pass
                for pid, pin in list(self.pins.items()):
                    try:
                        pin.update_leader()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def boundingRect(self):
        return self._rect

    def shape(self):
        # Include a small area around the control pivot in the item's clickable shape so
        # clicks on the pivot land on this node even though the visual pivot lies outside
        # the node's normal bounding rect.
        p = QPainterPath()
        p.addRect(self._rect)
        try:
            # Add a small hit area around the pivot (radius governed by PIVOT_HIT_RADIUS)
            pivot = getattr(self, '_pivot', None)
            if pivot is not None:
                r = PIVOT_HIT_RADIUS
                p.addEllipse(pivot.x() - r, pivot.y() - r, r * 2, r * 2)
        except Exception:
            pass
        return p

    def paint(self, painter, option, widget=None):
        # Visual style: render as two open wire ends (no device box)
        # The control pivot is represented by a child QGraphicsEllipseItem (self.control_pivot)
        # Keep painting minimal here; the visual pivot item handles its appearance and transforms.
        # If pivot highlight state changed, update the pivot's pen/brush accordingly.
        try:
            if getattr(self, 'control_pivot', None):
                if getattr(self, '_pivot_highlight', False):
                    self.control_pivot.setBrush(QBrush(SELECTED_COLOR))
                    self.control_pivot.setPen(QPen(SELECTED_COLOR, 1.6))
                else:
                    self.control_pivot.setBrush(Qt.NoBrush)
                    self.control_pivot.setPen(QPen(QColor(120, 120, 120), 1.2))
        except Exception:
            pass

    def _snap(self, v):
        return round(v / GRID_SIZE) * GRID_SIZE

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            try:
                # If the click is on/near the control pivot, we have two behaviors:
                # - Shift+LeftButton: relocate the pivot (user-driven reposition)
                # - LeftButton only: anchor node drag to the pivot (existing behavior)
                pivot_scene = self.mapToScene(getattr(self, '_pivot', self._rect.center()))
                click_scene = event.scenePos()
                # Distance threshold in scene coordinates (small tolerance for user clicks)
                dist_sq = (click_scene.x() - pivot_scene.x()) ** 2 + (click_scene.y() - pivot_scene.y()) ** 2

                # Pivot relocation (explicit): Shift+click on pivot begins pivot-dragging
                try:
                    # Also allow direct dot-press (no modifier) to relocate pivot for easier UI use
                    last_child = getattr(self, '_last_child_pressed', None)
                    if dist_sq <= (PIVOT_HIT_RADIUS * PIVOT_HIT_RADIUS) and (
                        (event.modifiers() & Qt.ShiftModifier) or (last_child == 'control_dot')
                    ):
                        self._pivot_dragging = True
                        self._pivot_drag_start_scene = pivot_scene
                        self._pivot_start_local = getattr(self, '_pivot', QPointF(0, 0))
                        # Lock pivot so auto-updates won't override user relocation
                        self._pivot_locked = True
                        try:
                            event.accept()
                        except Exception:
                            pass
                        return
                except Exception:
                    pass

                # Default pivot-anchored node drag behavior
                if dist_sq <= (PIVOT_HIT_RADIUS * PIVOT_HIT_RADIUS):
                    # Anchor drag to the pivot's scene coordinate
                    self._drag_start_pos = pivot_scene
                    self._item_start_pos = self.pos()
                else:
                    # Default: anchor to the actual click point
                    self._drag_start_pos = click_scene
                    self._item_start_pos = self.pos()
            except Exception:
                # Fallback to previous behavior if anything goes wrong
                self._drag_start_pos = event.scenePos()
                self._item_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Pivot relocation in progress
        try:
            if self._pivot_dragging and (event.buttons() & Qt.LeftButton):
                # Move pivot to mouse scene position, snapped to grid
                new_scene = event.scenePos()
                snapped_scene = QPointF(round(new_scene.x() / GRID_SIZE) * GRID_SIZE, round(new_scene.y() / GRID_SIZE) * GRID_SIZE)
                try:
                    self._pivot = self.mapFromScene(snapped_scene)
                    if getattr(self, 'control_pivot', None):
                        self.control_pivot.setPos(self._pivot)
                    if getattr(self, 'control_dot', None):
                        self.control_dot.setPos(self._pivot)
                    # Update leaders and attached bundles
                    for pid, pin in list(self.pins.items()):
                        try:
                            pin.update_leader()
                        except Exception:
                            pass
                    try:
                        for b in list(self.bundle_refs):
                            try:
                                b.update_geometry()
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
        except Exception:
            pass

        # Default node dragging behavior anchored to pivot or click point
        if self._drag_start_pos and (event.buttons() & Qt.LeftButton):
            delta = event.scenePos() - self._drag_start_pos
            # During interactive drags, compute snapped destination and set position accordingly
            try:
                snapped = QPointF(round((self._item_start_pos.x() + delta.x()) / GRID_SIZE) * GRID_SIZE,
                                  round((self._item_start_pos.y() + delta.y()) / GRID_SIZE) * GRID_SIZE)
                self.setPos(snapped)
            except Exception:
                try:
                    self.setPos(self._item_start_pos + delta)
                except Exception:
                    pass
            event.accept()
            return
        super().mouseMoveEvent(event)


    def setPos(self, *args, **kwargs):
        # Override to snap programmatic moves to GRID
        try:
            if len(args) == 1 and isinstance(args[0], QPointF):
                p = args[0]
            elif len(args) == 2:
                p = QPointF(args[0], args[1])
            else:
                return super().setPos(*args, **kwargs)
            snapped = QPointF(round(p.x() / GRID_SIZE) * GRID_SIZE, round(p.y() / GRID_SIZE) * GRID_SIZE)
            return super().setPos(snapped)
        except Exception:
            return super().setPos(*args, **kwargs)
            new_pos = self._item_start_pos + delta
            new_pos.setX(self._snap(new_pos.x()))
            new_pos.setY(self._snap(new_pos.y()))
            self.setPos(new_pos)
            if callable(self.on_changed):
                self.on_changed()
            event.accept()
            return
        event.ignore()

    def mouseReleaseEvent(self, event):
        # End pivot relocation if in progress
        try:
            if self._pivot_dragging and event.button() == Qt.LeftButton:
                self._pivot_dragging = False
                self._pivot_drag_start_scene = None
                self._pivot_start_local = None
                try:
                    event.accept()
                except Exception:
                    pass
                # Keep pivot locked (user preference) until explicitly reset
        except Exception:
            pass

        self._drag_start_pos = None
        self._item_start_pos = None
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneChange:
            # Ensure pins align to the global grid once this node is added to a scene
            if value:
                try:
                    self._enforce_pin_grid()
                except Exception:
                    pass

        if change == QGraphicsItem.ItemSelectedHasChanged:
            # Highlight control pivot ellipse when node is selected (no rectangular halos)
            try:
                if getattr(self, 'control_pivot', None):
                    if value:
                        # Enforce selected appearance (overrides bundle suppression)
                        # Keep pivot at the fixed device-space size; fill with selected color
                        try:
                            r = CONTROL_PIVOT_DIAM / 2.0
                            self.control_pivot.setRect(-r, -r, CONTROL_PIVOT_DIAM, CONTROL_PIVOT_DIAM)
                        except Exception:
                            pass
                        self.control_pivot.setBrush(QBrush(SELECTED_COLOR))
                        self.control_pivot.setPen(QPen(SELECTED_COLOR, 1.6))
                        # Update and show selection ring and label (ensure they stay centered)
                        try:
                            if getattr(self, 'control_pivot_ring', None):
                                ring_r = r + SELECTED_RING_PAD
                                ring_d = ring_r * 2
                                # center ring on the pivot
                                self.control_pivot_ring.setRect(-ring_r, -ring_r, ring_d, ring_d)
                                self.control_pivot_ring.setPos(self._pivot)
                                self.control_pivot_ring.setVisible(True)
                            if getattr(self, 'control_pivot_label', None):
                                br = self.control_pivot_label.boundingRect()
                                # place label just outside the ring on the right
                                self.control_pivot_label.setPos(self._pivot + QPointF(ring_r + 6, -br.height() / 2))
                                self.control_pivot_label.setVisible(True)
                        except Exception:
                            pass
                    else:
                        # Deselected: revert sizes and visuals
                        try:
                            r = CONTROL_PIVOT_DIAM / 2.0
                            self.control_pivot.setRect(-r, -r, CONTROL_PIVOT_DIAM, CONTROL_PIVOT_DIAM)
                        except Exception:
                            pass
                        # Restore default filled dark blue when not selected
                        try:
                            self.control_pivot.setBrush(QBrush(PIVOT_COLOR))
                        except Exception:
                            self.control_pivot.setBrush(Qt.NoBrush)
                        self.control_pivot.setPen(Qt.NoPen)
                        # Recompute ring geometry to default and hide visuals
                        try:
                            if getattr(self, 'control_pivot_ring', None):
                                r = CONTROL_PIVOT_DIAM / 2.0
                                ring_r = r + SELECTED_RING_PAD
                                ring_d = ring_r * 2
                                self.control_pivot_ring.setRect(-ring_r, -ring_r, ring_d, ring_d)
                                self.control_pivot_ring.setPos(self._pivot)
                                self.control_pivot_ring.setVisible(False)
                            if getattr(self, 'control_pivot_label', None):
                                br = self.control_pivot_label.boundingRect()
                                self.control_pivot_label.setPos(self._pivot + QPointF(ring_r + 6, -br.height() / 2))
                                self.control_pivot_label.setVisible(False)
                        except Exception:
                            pass
                # Mirror selection on the always-visible control_dot so it is more noticeable,
                # but suppress it while a bundle is attached (bundle has precedence).
                if getattr(self, 'control_dot', None):
                    try:
                        if getattr(self, 'bundle_refs', None):
                            # If bundle attached, ensure control_dot remains hidden (no brush).
                            self.control_dot.setBrush(Qt.NoBrush)
                        else:
                            if value:
                                # Slightly enlarge the dot for selected state
                                try:
                                    new_dot = CONTROL_DOT_DIAM + 2
                                    dr = new_dot / 2.0
                                    self.control_dot.setRect(-dr, -dr, new_dot, new_dot)
                                except Exception:
                                    pass
                                self.control_dot.setBrush(QBrush(SELECTED_COLOR))
                            else:
                                try:
                                    dr = CONTROL_DOT_DIAM / 2.0
                                    self.control_dot.setRect(-dr, -dr, CONTROL_DOT_DIAM, CONTROL_DOT_DIAM)
                                except Exception:
                                    pass
                                self.control_dot.setBrush(QBrush(QColor(180, 180, 180)))
                    except Exception:
                        pass
                self.update()
            except Exception:
                pass

        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update pivot and handle movement delta
            new_pos = value if isinstance(value, QPointF) else self.pos()
            prev = getattr(self, '_prev_pos', None)
            if prev is None:
                self._prev_pos = new_pos
                delta = QPointF(0, 0)
            else:
                delta = QPointF(new_pos.x() - prev.x(), new_pos.y() - prev.y())
                self._prev_pos = new_pos

            if callable(self.on_changed):
                self.on_changed()
            # Notify attached bundles about movement so they can adjust
            try:
                for b in list(self.bundle_refs):
                    if b:
                        try:
                            if callable(getattr(b, 'node_moved', None)):
                                b.node_moved(self, delta)
                        except Exception:
                            pass
                        b.update_geometry()
            except Exception:
                pass
        return super().itemChange(change, value)


class TwistedBundleItem(QGraphicsPathItem):
    """Double-helix visual connecting two TwistNodeItems with a single elbow handle."""

    def __init__(self, source_node: TwistNodeItem, target_node: TwistNodeItem, on_changed=None, on_delete=None):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.on_changed = on_changed
        self.on_delete = on_delete

        self.amplitude = 5.0
        self.wavelength = 40.0
        self.samples = 60

        self.color_a = QColor(255, 80, 80)
        self.color_b = QColor(80, 180, 255)

        # Route points (elbow list). Each element is a (x, y) tuple in scene coords.
        self.route: list[tuple[float, float]] = []

        self.path_a = QPainterPath()
        self.path_b = QPainterPath()

        # No bundle-wide halo path; selection highlights will be applied to node control pivots
        self.halo_path = None

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-0.8)

        s = self._start_point()
        e = self._end_point()
        self.elbow_pos = QPointF((s.x() + e.x()) / 2, (s.y() + e.y()) / 2)

        # Implicit main handle removed: do not create a separate ellipse control here.
        # Users create explicit elbows via double-click (add_elbow_at) which will create
        # ElbowHandle items. Keeping an implicit handle caused stray visuals that could
        # appear detached from the bundle during interactive edits.
        pass

        # Elbow & segment handles for interactive editing
        self.elbow_handles: list[ElbowHandle] = []
        self.segment_handles: list[SegmentHandle] = []

        # Endpoint markers removed: they were causing orphaned, unconnected ellipses.
        # Keep attributes absent (None) so older code that checks for presence continues to work.
        self.start_marker = None
        self.end_marker = None

        # Recompute geometry as usual
        self.recalculate_path()

        # Register this bundle with the nodes so node-side events (e.g. wire recolor) can
        # notify the bundle even if creation didn't happen via the higher-level app helper.
        if hasattr(self.source_node, 'register_bundle'):
            self.source_node.register_bundle(self)
        if hasattr(self.target_node, 'register_bundle'):
            self.target_node.register_bundle(self)

        # Finalize attachment deterministically: compute which side each node reserves for
        # the bundle based on node positions and perform a single, deterministic update pass
        # so pins, pivots and leaders are all in a stable consistent state.
        try:
            self.finalize_attachment()
        except Exception:
            pass

    def finalize_attachment(self):
        """Deterministically set _bundle_side on both nodes and refresh pins/pivots/leaders.
        This avoids transient or order-dependent side computation and stabilizes leader endpoints."""
        try:
            a = self.source_node
            b = self.target_node
            if not a or not b:
                return
            apos = a.pos()
            bpos = b.pos()
            # Decide side by largest component, consistent for both nodes
            if abs(bpos.x() - apos.x()) >= abs(bpos.y() - apos.y()):
                if bpos.x() > apos.x():
                    a._bundle_side = Side.RIGHT
                    b._bundle_side = Side.LEFT
                else:
                    a._bundle_side = Side.LEFT
                    b._bundle_side = Side.RIGHT
            else:
                if bpos.y() > apos.y():
                    a._bundle_side = Side.BOTTOM
                    b._bundle_side = Side.TOP
                else:
                    a._bundle_side = Side.TOP
                    b._bundle_side = Side.BOTTOM

            # Rebuild and refresh both nodes
            for n in (a, b):
                try:
                    n._build_pins()
                    n._enforce_pin_grid()
                    n._update_pivot_from_pins()
                    if getattr(n, 'control_pivot', None):
                        try:
                            n.control_pivot.setPos(n._pivot)
                        except Exception:
                            pass
                    for pid, pin in list(n.pins.items()):
                        try:
                            pin.update_leader()
                        except Exception:
                            pass
                except Exception:
                    pass
            # Rebuild geometry for bundle last
            try:
                self.update_geometry()
            except Exception:
                pass
            # Ensure leaders are refreshed one more time after geometry rebuild to avoid transient stale endpoints
            for n in (a, b):
                try:
                    for pid, pin in list(n.pins.items()):
                        try:
                            pin.update_leader()
                        except Exception:
                            pass
                except Exception:
                    pass
            # Propagate bundle colors to connected node pins so pins/leaders visually match the bundle
            try:
                self._apply_colors_to_nodes()
            except Exception:
                pass
        except Exception:
            pass

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        menu.addAction("Delete Bundle", self._delete_via_menu)
        menu.exec(event.screenPos())

    def _delete_via_menu(self):
        # If an owner callback is present, call it; otherwise perform local deletion
        if callable(self.on_delete):
            try:
                self.on_delete(self)
                return
            except Exception:
                pass
        # Default deletion: unregister from nodes and remove from scene
        if hasattr(self.source_node, 'unregister_bundle'):
            self.source_node.unregister_bundle(self)
        if hasattr(self.target_node, 'unregister_bundle'):
            self.target_node.unregister_bundle(self)
        if self.scene():
            self.scene().removeItem(self)
        if callable(self.on_changed):
            self.on_changed()

    def _start_point(self):
        # Control node center (pivot) is the bundle connection point (scene coords)
        try:
            return self.source_node.mapToScene(getattr(self.source_node, '_pivot', self.source_node._rect.center()))
        except Exception:
            # Fallback to H/L midpoint
            h = self.source_node.get_pin_tip_scene_pos("H")
            l = self.source_node.get_pin_tip_scene_pos("L")
            return QPointF((h.x() + l.x()) / 2, (h.y() + l.y()) / 2)

    def _end_point(self):
        try:
            return self.target_node.mapToScene(getattr(self.target_node, '_pivot', self.target_node._rect.center()))
        except Exception:
            h = self.target_node.get_pin_tip_scene_pos("H")
            l = self.target_node.get_pin_tip_scene_pos("L")
            return QPointF((h.x() + l.x()) / 2, (h.y() + l.y()) / 2)

    def _poly_points(self):
        # Build polyline including start, a short segment to the node pivot (edit grip),
        # any route elbows, and end.
        pts = []
        start = self._start_point()
        pts.append(start)
        # Insert a pivot point near the node so the bundle bends around the edit node
        try:
            p1 = self.source_node.mapToScene(getattr(self.source_node, '_pivot', self.source_node._rect.center()))
            pts.append(p1)
        except Exception:
            pass

        for x, y in self.route:
            pts.append(QPointF(x, y))

        try:
            p2 = self.target_node.mapToScene(getattr(self.target_node, '_pivot', self.target_node._rect.center()))
            pts.append(p2)
        except Exception:
            pass
        end = self._end_point()
        pts.append(end)
        return pts

    def _poly_points(self):
        # Build polyline including start, route elbows, and end
        pts = [self._start_point()]
        for x, y in self.route:
            pts.append(QPointF(x, y))
        pts.append(self._end_point())
        return pts

    def _segment_lengths(self, pts):
        lengths = []
        total = 0.0
        for i in range(len(pts) - 1):
            seg_len = QLineF(pts[i], pts[i + 1]).length()
            lengths.append(seg_len)
            total += seg_len
        return lengths, total

    def _point_at(self, pts, seg_lengths, total_len, t):
        if total_len == 0:
            return pts[0], QPointF(0, -1)
        target_dist = t * total_len
        acc = 0.0
        for i, seg_len in enumerate(seg_lengths):
            if seg_len == 0:
                continue
            if acc + seg_len >= target_dist:
                local_t = (target_dist - acc) / seg_len
                a, b = pts[i], pts[i + 1]
                x = a.x() + (b.x() - a.x()) * local_t
                y = a.y() + (b.y() - a.y()) * local_t
                dir_vec = QPointF(b.x() - a.x(), b.y() - a.y())
                return QPointF(x, y), dir_vec
            acc += seg_len
        return pts[-1], QPointF(0, -1)

    def _normal(self, dir_vec: QPointF):
        dx, dy = dir_vec.x(), dir_vec.y()
        if dx == 0 and dy == 0:
            return QPointF(0, -1)
        n = QPointF(-dy, dx)
        length = math.hypot(n.x(), n.y())
        if length == 0:
            return QPointF(0, -1)
        return QPointF(n.x() / length, n.y() / length)

    def recalculate_path(self, rebuild_handles: bool = True):
        pts = self._poly_points()
        seg_lengths, total_len = self._segment_lengths(pts)
        # Update any attached labels positions since path changed
        try:
            self._update_labels_positions(pts, seg_lengths, total_len)
        except Exception:
            pass
        if total_len == 0:
            base_path = QPainterPath(pts[0])
            self.path_a = base_path
            self.path_b = base_path
            self.setPath(base_path)
            if getattr(self, 'halo_path', None) is not None:
                self.halo_path.setPath(base_path)
            return

        step = 1.0 / max(self.samples - 1, 1)
        k = (2 * math.pi) / max(self.wavelength, 1.0)

        def build_path(phase_shift):
            p0, _ = self._point_at(pts, seg_lengths, total_len, 0.0)
            path = QPainterPath(p0)
            for i in range(1, self.samples):
                t = i * step
                base_pt, dir_vec = self._point_at(pts, seg_lengths, total_len, t)
                n = self._normal(dir_vec)
                phase = k * (t * total_len) + phase_shift
                offset = math.sin(phase) * self.amplitude
                offset_pt = QPointF(base_pt.x() + n.x() * offset, base_pt.y() + n.y() * offset)
                path.lineTo(offset_pt)
            return path

        self.path_a = build_path(0.0)
        self.path_b = build_path(math.pi)

        # Envelope path for selection/hit area
        env = QPainterPath(self.path_a.pointAtPercent(0))
        env.addPath(self.path_a)
        env.addPath(self.path_b)
        self.setPath(env)
        # Do not set or display a global halo path for bundles; selection highlights will be shown
        # on the node control pivot ellipses instead.
        self._update_colors_from_nodes()

        # Rebuild elbow handles to reflect any route edits (optional during interactive drags)
        if rebuild_handles:
            self._rebuild_elbow_handles()
        else:
            # Update positions of existing handles to keep them attached during interactive operations
            self._update_elbow_handle_positions()
        # Update endpoint markers positions
        try:
            self.start_marker.setPos(self.mapFromScene(self._start_point()))
            self.end_marker.setPos(self.mapFromScene(self._end_point()))
            # Ensure markers remain hollow outlines
            try:
                self.start_marker.setBrush(Qt.NoBrush)
                self.end_marker.setBrush(Qt.NoBrush)
            except Exception:
                pass
        except Exception:
            pass

        # Reconcile node pivots and pin leaders so bundle geometry changes are reflected
        try:
            for n in (self.source_node, self.target_node):
                try:
                    n._enforce_pin_grid()
                    n._update_pivot_from_pins()
                    for pid, pin in list(n.pins.items()):
                        try:
                            pin.update_leader()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def _update_labels_positions(self, pts, seg_lengths, total_len):
        # Ensure corresponding label_items exist and position them along the path
        print(f"ENTER _update_labels_positions pts={pts} seg_lengths={seg_lengths} total_len={total_len}")
        try:
            # Lazy-create label_items list to align with model.labels
            if not hasattr(self, 'label_items'):
                self.label_items = []
            # Remove any excess items if model shrank
            while len(self.label_items) > len(getattr(self.model, 'labels', [])):
                it = self.label_items.pop()
                try:
                    if it.scene():
                        it.scene().removeItem(it)
                except Exception:
                    pass
            # Iterate and create/update
            for idx, lbl in enumerate(getattr(self.model, 'labels', [])):
                if idx >= len(self.label_items):
                    itm = WireLabelItem(lbl, self)
                    self.label_items.append(itm)
                else:
                    itm = self.label_items[idx]
                    itm.model = lbl
                try:
                    pt, dir_vec = self._point_at(pts, seg_lengths, total_len, lbl.t_pos)
                    itm.setPos(self.mapFromScene(pt))
                except Exception:
                    pass
        except Exception:
            pass

    def shape(self):
        # Return the shape for hit-testing, but subtract small circular holes around
        # the bundle endpoints so clicks on node control pivots don't hit the bundle.
        try:
            base = QPainterPath(self.path())
            r = PIVOT_HIT_RADIUS
            try:
                sp = self._start_point()
                hole = QPainterPath()
                hole.addEllipse(sp.x() - r, sp.y() - r, r * 2, r * 2)
                base = base.subtracted(hole)
            except Exception:
                pass
            try:
                ep = self._end_point()
                hole = QPainterPath()
                hole.addEllipse(ep.x() - r, ep.y() - r, r * 2, r * 2)
                base = base.subtracted(hole)
            except Exception:
                pass
            return base
        except Exception:
            return QPainterPath(self.path())

    def _snap_point(self, pt: QPointF) -> QPointF:
        return QPointF(round(pt.x() / GRID_SIZE) * GRID_SIZE, round(pt.y() / GRID_SIZE) * GRID_SIZE)

    def _segment_insert_index(self, pt: QPointF, nodes):
        best_idx = 0
        best_dist = float('inf')
        for i in range(len(nodes) - 1):
            a = nodes[i]
            b = nodes[i+1]
            ab = b - a
            denom = ab.x() * ab.x() + ab.y() * ab.y()
            t = 0.0 if denom == 0 else ((pt - a).x() * ab.x() + (pt - a).y() * ab.y()) / denom
            t = max(0.0, min(1.0, t))
            proj = QPointF(a.x() + ab.x() * t, a.y() + ab.y() * t)
            dist = QLineF(pt, proj).length()
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return best_idx
        if total_len == 0:
            base_path = QPainterPath(pts[0])
            self.path_a = base_path
            self.path_b = base_path
            self.setPath(base_path)
            self.halo_path.setPath(base_path)
            return

        step = 1.0 / max(self.samples - 1, 1)
        k = (2 * math.pi) / max(self.wavelength, 1.0)

        def build_path(phase_shift):
            p0, _ = self._point_at(pts, seg_lengths, total_len, 0.0)
            path = QPainterPath(p0)
            for i in range(1, self.samples):
                t = i * step
                base_pt, dir_vec = self._point_at(pts, seg_lengths, total_len, t)
                n = self._normal(dir_vec)
                phase = k * (t * total_len) + phase_shift
                offset = math.sin(phase) * self.amplitude
                offset_pt = QPointF(base_pt.x() + n.x() * offset, base_pt.y() + n.y() * offset)
                path.lineTo(offset_pt)
            return path

        self.path_a = build_path(0.0)
        self.path_b = build_path(math.pi)

        # Envelope path for selection/hit area
        env = QPainterPath(self.path_a.pointAtPercent(0))
        env.addPath(self.path_a)
        env.addPath(self.path_b)
        self.setPath(env)
        if getattr(self, 'halo_path', None) is not None:
            self.halo_path.setPath(env)
        self._update_colors_from_nodes()
        # Rebuild elbow handles to reflect any route edits
        self._rebuild_elbow_handles()

    def _update_colors_from_nodes(self):
        # Look for colors attached to High/Low pins on either node (prefer source then target)
        c_high = self.source_node.first_wire_color("H") or self.target_node.first_wire_color("H")
        c_low = self.source_node.first_wire_color("L") or self.target_node.first_wire_color("L")
        if isinstance(c_high, QColor):
            self.color_a = c_high
        if isinstance(c_low, QColor):
            self.color_b = c_low
        # After updating, ensure connected node pins reflect these colors
        try:
            self._apply_colors_to_nodes()
        except Exception:
            pass

    def _blend_colors(self, ca: QColor, cb: QColor) -> QColor:
        try:
            r = (ca.red() + cb.red()) // 2
            g = (ca.green() + cb.green()) // 2
            b = (ca.blue() + cb.blue()) // 2
            return QColor(r, g, b)
        except Exception:
            return ca

    def _apply_colors_to_nodes(self):
        # Apply bundle colors to each node's pins: H -> color_a, L -> color_b, S -> blend
        for node, swap in ((self.source_node, False), (self.target_node, True)):
            try:
                for pid, pin in list(node.pins.items()):
                    if pid == 'H':
                        color = self.color_a
                    elif pid == 'L':
                        color = self.color_b
                    else:  # 'S' shield
                        color = self._blend_colors(self.color_a, self.color_b)
                    try:
                        pin.set_color(color)
                        pin.update_leader()
                    except Exception:
                        pass
            except Exception:
                pass

    def paint(self, painter, option, widget=None):
        pen_a = QPen(self.color_a, WIRE_THICKNESS)
        pen_b = QPen(self.color_b, WIRE_THICKNESS)
        pen_a.setCapStyle(Qt.RoundCap)
        pen_b.setCapStyle(Qt.RoundCap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen_a)
        painter.drawPath(self.path_a)
        painter.setPen(pen_b)
        painter.drawPath(self.path_b)

    def _rebuild_elbow_handles(self):
        # Remove old
        for h in list(getattr(self, 'elbow_handles', [])) + list(getattr(self, 'segment_handles', [])):
            if h.scene():
                h.scene().removeItem(h)
        self.elbow_handles = []
        self.segment_handles = []

        # Create elbow handles for route points
        for idx, (x, y) in enumerate(self.route):
            handle = ElbowHandle(self, idx)
            handle.setParentItem(self)
            # Position handle using parent's coordinates
            handle.setPos(self.mapFromScene(QPointF(x, y)))
            # override handle context menu to delete
            def _ctx(ev, index=idx):
                self.delete_elbow(index)
                ev.accept()
            handle.contextMenuEvent = _ctx
            self.elbow_handles.append(handle)

        # Create segment handles between poly points
        pts = self._poly_points()
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i+1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            sh = SegmentHandle(self, i, p1, p2)
            sh.setParentItem(self)
            sh.setPos(self.mapFromScene(mid))
            self.segment_handles.append(sh)

    def _update_elbow_handle_positions(self):
        # Update existing handle positions (parent-local coordinates) without recreating items.
        # Ensure segment handles exist for the current polyline even if there are no elbows
        try:
            pts = self._poly_points()
            if len(self.segment_handles) != max(0, len(pts) - 1):
                self._rebuild_elbow_handles()
                return
        except Exception:
            pass
        # Keep the same handle counts; if topology changed, request a rebuild instead.
        if len(self.elbow_handles) != len(self.route):
            self._rebuild_elbow_handles()
            return
        # Update elbow handles
        for idx, handle in enumerate(self.elbow_handles):
            x, y = self.route[idx]
            handle.setPos(self.mapFromScene(QPointF(x, y)))
            if HANDLE_DEBUG:
                scene_pos = handle.mapToScene(handle.boundingRect().center())
                print(f"DEBUG Bundle._update_elbow_handle_positions: elbow idx={idx} route=({x},{y}) handle_scene={scene_pos} handle_local={handle.pos()}")
            # Correction watchdog: ensure handle matches model route precisely to avoid visual orphaning
            try:
                scene_pos = handle.mapToScene(handle.boundingRect().center())
                route_scene = QPointF(x, y)
                dx = scene_pos.x() - route_scene.x()
                dy = scene_pos.y() - route_scene.y()
                if (dx*dx + dy*dy) ** 0.5 > 1.0:
                    handle.setPos(self.mapFromScene(route_scene))
                    handle.update()
                    try:
                        sc = self.scene()
                        if sc:
                            sc.update()
                            for v in sc.views():
                                try:
                                    v.viewport().repaint()
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    if HANDLE_DEBUG or HANDLE_DEBUG_VERBOSE:
                        print(f"WATCHDOG: corrected bundle elbow idx={idx} from {scene_pos} to {route_scene}")
            except Exception:
                pass
        # Update segment handles
        pts = self._poly_points()
        if len(self.segment_handles) != max(0, len(pts) - 1):
            self._rebuild_elbow_handles()
            return
        for i, sh in enumerate(self.segment_handles):
            p1, p2 = pts[i], pts[i+1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            sh.setPos(self.mapFromScene(mid))

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            # Do not display a global halo path for bundles; instead highlight the node control pivots
            # Change endpoint marker outline color when selected so user sees the bundle is active
            try:
                if getattr(self, 'start_marker', None):
                    # Keep endpoint markers as hollow rings; only change outline color on select
                    try:
                        self.start_marker.setBrush(Qt.NoBrush)
                        if value:
                            self.start_marker.setPen(QPen(SELECTED_COLOR, 1.6))
                        else:
                            self.start_marker.setPen(QPen(QColor(140, 140, 140), 1.6))
                    except Exception:
                        pass
                if getattr(self, 'end_marker', None):
                    try:
                        self.end_marker.setBrush(Qt.NoBrush)
                        if value:
                            self.end_marker.setPen(QPen(SELECTED_COLOR, 1.6))
                        else:
                            self.end_marker.setPen(QPen(QColor(140, 140, 140), 1.6))
                    except Exception:
                        pass
            except Exception:
                pass
            # Highlight node pivots when the bundle is selected (so halo surrounds control pivot only)
            try:
                if value:
                    self.source_node._pivot_highlight = True
                    self.target_node._pivot_highlight = True
                else:
                    self.source_node._pivot_highlight = False
                    self.target_node._pivot_highlight = False
                # Update pivot visuals immediately. When the bundle is selected we show an outline
                # on the node pivot (no fill) to indicate the bundle's connection without taking
                # over the node's selected appearance (avoid filled orange on the nodes).
                try:
                    if getattr(self.source_node, 'control_pivot', None):
                        if value:
                            self.source_node.control_pivot.setBrush(Qt.NoBrush)
                            self.source_node.control_pivot.setPen(QPen(SELECTED_COLOR, 1.6))
                        else:
                            self.source_node.control_pivot.setBrush(Qt.NoBrush)
                            self.source_node.control_pivot.setPen(QPen(QColor(120, 120, 120), 1.2))
                except Exception:
                    pass
                try:
                    if getattr(self.target_node, 'control_pivot', None):
                        if value:
                            self.target_node.control_pivot.setBrush(Qt.NoBrush)
                            self.target_node.control_pivot.setPen(QPen(SELECTED_COLOR, 1.6))
                        else:
                            self.target_node.control_pivot.setBrush(Qt.NoBrush)
                            self.target_node.control_pivot.setPen(QPen(QColor(120, 120, 120), 1.2))
                except Exception:
                    pass
                self.source_node.update()
                self.target_node.update()
            except Exception:
                pass
        return super().itemChange(change, value)

    def update_geometry(self, rebuild_handles: bool = True):
        self.recalculate_path(rebuild_handles=rebuild_handles)
        # Ensure colors are refreshed after any external changes (e.g. wire recolor)
        self._update_colors_from_nodes()
        # If callers asked to avoid rebuilding handles but handles appear missing or out-of-date,
        # rebuild them to avoid transient missing-handle states (helps tests and deterministic layout).
        if not rebuild_handles:
            try:
                pts = self._poly_points()
                if len(self.segment_handles) != max(0, len(pts) - 1) or len(self.elbow_handles) != len(self.route):
                    self._rebuild_elbow_handles()
            except Exception:
                pass
        # No implicit handle to position; optionally dump nearby items if debug enabled
        if HANDLE_DEBUG_VERBOSE:
            try:
                sc = self.scene()
                if sc:
                    rect = QRectF(self.elbow_pos.x() - 4, self.elbow_pos.y() - 4, 8, 8)
                    nearby = sc.items(rect)
                    entries = []
                    for it in nearby:
                        data = None
                        try:
                            data = it.data(0)
                        except Exception:
                            data = None
                        entries.append((it.__class__.__name__, data, it.parentItem().__class__.__name__ if it.parentItem() else None))
                    print(f"VERBOSE Bundle.debug_near_elbow: elbow_pos={self.elbow_pos} nearby={entries}")
            except Exception:
                pass
        self.update()
        if callable(self.on_changed):
            self.on_changed()

    def set_elbow(self, scene_pos: QPointF):
        snapped = self._snap_point(scene_pos)
        # If there are no route points, preserve single-handle behavior by treating this as the sole route
        if not self.route:
            self.route = [(snapped.x(), snapped.y())]
        else:
            # move the midpoint (use index in middle)
            mid_idx = len(self.route) // 2
            self.route[mid_idx] = (snapped.x(), snapped.y())
        self.elbow_pos = snapped
        # During interactive drags, avoid rebuilding handles (preserve the handle being dragged)
        self.update_geometry(rebuild_handles=False)

    def add_elbow_at(self, pt: QPointF):
        pt = QPointF(round(pt.x() / GRID_SIZE) * GRID_SIZE, round(pt.y() / GRID_SIZE) * GRID_SIZE)
        pts = self._poly_points()
        if len(pts) < 2:
            return
        idx = self._segment_insert_index(pt, pts)
        self.route.insert(idx, (pt.x(), pt.y()))
        self.update_geometry()

    def move_elbow(self, index: int, pt: QPointF):
        if index < 0 or index >= len(self.route):
            return
        pt = self._snap_point(pt)
        self.route[index] = (pt.x(), pt.y())
        self.elbow_pos = QPointF(pt.x(), pt.y())
        # During interactive drags, avoid rebuilding handles which can remove the handle under the cursor
        self.update_geometry(rebuild_handles=False)

    def move_segment_handle(self, segment_index: int, new_mid: QPointF, anchor_mid: QPointF, original_route: list | None = None):
        pts = self._poly_points()
        if segment_index < 0 or segment_index >= len(pts) - 1:
            return
        new_mid = self._snap_point(new_mid)
        delta = QPointF(new_mid.x() - anchor_mid.x(), new_mid.y() - anchor_mid.y())
        if delta.isNull():
            return
        start_is_pin = segment_index == 0
        end_is_pin = (segment_index + 1) == (len(pts) - 1)

        if original_route is not None:
            # Use the press-time snapshot as a stable baseline to avoid non-monotonic jumps
            new_route = list(original_route)
            if not start_is_pin:
                ridx = segment_index - 1
                if 0 <= ridx < len(new_route):
                    new_route[ridx] = (original_route[ridx][0] + delta.x(), original_route[ridx][1] + delta.y())
            if not end_is_pin:
                ridx = segment_index
                if 0 <= ridx < len(new_route):
                    new_route[ridx] = (original_route[ridx][0] + delta.x(), original_route[ridx][1] + delta.y())
            self.route = new_route
            if HANDLE_DEBUG or HANDLE_DEBUG_VERBOSE:
                print(f"DEBUG Bundle.move_segment_handle (snapshot): seg={segment_index} delta=({delta.x()},{delta.y()}) original_len={len(original_route)} new_route={self.route} start_is_pin={start_is_pin} end_is_pin={end_is_pin}")
                if HANDLE_DEBUG_VERBOSE:
                    print(f"VERBOSE Bundle.move_segment_handle: original_route={original_route}")
        else:
            # Only move route points (elbows) that abut this segment (fallback incremental behavior)
            if not start_is_pin:
                ridx = segment_index - 1
                self.route[ridx] = (self.route[ridx][0] + delta.x(), self.route[ridx][1] + delta.y())
            if not end_is_pin:
                ridx = segment_index
                if ridx < len(self.route):
                    self.route[ridx] = (self.route[ridx][0] + delta.x(), self.route[ridx][1] + delta.y())
            if HANDLE_DEBUG:
                print(f"DEBUG Bundle.move_segment_handle (incremental): seg={segment_index} delta=({delta.x()},{delta.y()}) route={self.route}")
        # Avoid rebuilding handles mid-drag
        self.update_geometry(rebuild_handles=False)

    def delete_elbow(self, index: int):
        if index < 0 or index >= len(self.route):
            return
        self.route.pop(index)
        # update elbow_pos to midpoint if any remain
        if self.route:
            mid = self.route[len(self.route)//2]
            self.elbow_pos = QPointF(mid[0], mid[1])
        else:
            s = self._start_point(); e = self._end_point();
            self.elbow_pos = QPointF((s.x()+e.x())/2, (s.y()+e.y())/2)
        self.update_geometry()

    def node_moved(self, node, delta: QPointF):
        """Called when a connected TwistNode moves. Translate route points or implicit elbow by delta
        so the bundle follows the device movement in an intuitive way.
        """
        if not delta or (delta.x() == 0 and delta.y() == 0):
            return
        if not self.route:
            # No user-defined elbows -> just move the implicit elbow
            self.elbow_pos = QPointF(self.elbow_pos.x() + delta.x(), self.elbow_pos.y() + delta.y())
        else:
            self.route = [(x + delta.x(), y + delta.y()) for (x, y) in self.route]
        # After modifying, ensure geometry is updated
        # Avoid rebuilding handles during node movement to keep handles attached
        self.update_geometry(rebuild_handles=False)

    # Hook handle movement to elbow updates
    def mouseMoveEvent(self, event):
        # Implicit dragging of a main handle was removed. Users can add elbows (double-click)
        # and then drag those explicit elbow handles to edit their position.
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Add an elbow where the user double-clicks on the bundle
        try:
            self.add_elbow_at(event.scenePos())
            event.accept()
        except Exception:
            pass


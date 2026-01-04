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
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QAction, QPainterPath, QPainterPathStroker
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, QTimer
from talustrace.backend.models import Side
from talustrace.backend.sizer import AutoSizer
from talustrace.backend.printer import Printer
from talustrace.backend.labels import LabelManager

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
SEGMENT_HANDLE_COLOR = QColor(180, 180, 180)
TEXT_INSET = 6
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
        self.setRect(-8, -8, 16, 16)
        self.setBrush(Qt.NoBrush)
        self.setPen(Qt.NoPen)
        self.line = QGraphicsLineItem(self)
        self.line.setPen(QPen(PIN_COLOR, 3))
        self.setAcceptHoverEvents(True)
    def set_visual_geometry(self, x1, y1, x2, y2):
        self.setPos(x1, y1)
        self.line.setLine(0, 0, x2-x1, y2-y1)
    def hoverEnterEvent(self, event):
        self.line.setPen(QPen(PIN_HOVER_COLOR, 3))
        super().hoverEnterEvent(event)
    def hoverLeaveEvent(self, event):
        self.line.setPen(QPen(PIN_COLOR, 2))
        super().hoverLeaveEvent(event)
    def get_scene_pos(self):
        return self.mapToScene(0, 0)

    def get_tip_scene_pos(self):
        # Tip is the end of the drawn pin line, in scene coords
        return self.line.mapToScene(self.line.line().p2())

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
        
        # Selection Halo (Sibling Item)
        self.halo = QGraphicsRectItem() # No parent
        self.halo.setPen(QPen(SELECTED_COLOR, 4))
        self.halo.setBrush(Qt.NoBrush)
        self.halo.hide()
        self.halo.setZValue(-1) # Behind the device box

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
        # Remove existing pin graphics before rebuild
        for pin in self.pins.values():
            if pin.scene():
                pin.scene().removeItem(pin)
        self.pins = {}

        # Use Backend AutoSizer for dimensions
        width, height = AutoSizer.calculate_size(self.model)
        
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, width, height)
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
            if value: value.addItem(self.halo)
            elif self.halo.scene(): self.halo.scene().removeItem(self.halo)

        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.halo.setVisible(value)
            if value: self.halo.setPos(self.pos())

        if change == QGraphicsItem.ItemPositionHasChanged:
             self.halo.setPos(self.pos())
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

class ElbowHandle(QGraphicsEllipseItem):
    def __init__(self, wire_item, index):
        super().__init__(-6, -6, 12, 12)
        self.wire_item = wire_item
        self.index = index
        self.setBrush(QBrush(ELBOW_COLOR))
        self.setPen(Qt.NoPen)
        # Keep size fixed on zoom; still accept drags so we can drive model updates.
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setZValue(3)

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
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setZValue(2)
        self._anchor_mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)

    def mouseMoveEvent(self, event):
        new_mid = event.scenePos()
        self.wire_item.move_segment_handle(self.segment_index, new_mid, self._anchor_mid)
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return self.pos()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        # refresh anchor after a completed drag
        if self.wire_item:
            nodes = self.wire_item._build_nodes()
            if self.segment_index < len(nodes) - 1:
                p1, p2 = nodes[self.segment_index], nodes[self.segment_index + 1]
                self._anchor_mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
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

        self.twist_path = QGraphicsPathItem(self)
        self.twist_path.setZValue(-0.5)
        self.twist_path.hide()

        self.segment_handles = []
        self.elbow_handles = []

        if self.source_dev:
            self.source_dev.attached_wires.append(self)
        if self.target_dev:
            self.target_dev.attached_wires.append(self)

        self.update_visuals()
        self.update_geometry()
        self.refresh_metadata()

    def contextMenuEvent(self, event):
        menu = QMenu()
        twist_action = QAction("Twisted Pair", menu)
        twist_action.setCheckable(True)
        twist_action.setChecked(self.model.twisted)

        def _toggle_twist(checked=False):
            self.model.twisted = bool(checked)
            _record_action_usage("wire.twisted")
            self.update_visuals()
            self.update_geometry()
            self._update_tooltip()
            self._notify_changed()

        twist_action.triggered.connect(_toggle_twist)
        entries = [
            ("wire.delete", "Delete Wire", self._delete_wire_confirm),
        ]

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

        menu.addAction(twist_action)
        menu.addSeparator()

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
        self.setPen(QPen(base_color, 3))
        self.halo_path.setPen(QPen(SELECTED_COLOR, 6))

        overlay_color = QColor(base_color)
        overlay_color = overlay_color.lighter(135)
        twist_pen = QPen(overlay_color, 2, Qt.DashDotLine)
        twist_pen.setCapStyle(Qt.RoundCap)
        twist_pen.setJoinStyle(Qt.RoundJoin)
        self.twist_path.setPen(twist_pen)

    def refresh_metadata(self):
        start_meta = getattr(self.source_dev.model, "meta", {}) if self.source_dev else {}
        end_meta = getattr(self.target_dev.model, "meta", {}) if self.target_dev else {}
        src_pin = self.source_dev.pins.get(self.src_pin_id) if self.source_dev else None
        tgt_pin = self.target_dev.pins.get(self.tgt_pin_id) if self.target_dev else None
        src_meta = getattr(src_pin.model, "meta", {}) if src_pin else {}
        tgt_meta = getattr(tgt_pin.model, "meta", {}) if tgt_pin else {}

        # Preserve existing custom meta, then overlay device/pin meta (end pin wins conflicts)
        merged = {**(self.model.meta or {}), **start_meta, **end_meta, **src_meta, **tgt_meta}
        self.model.meta = merged
        self._update_tooltip()

    def _update_tooltip(self):
        def fmt_endpoint(dev, pin_id):
            if not dev:
                return "?"
            dev_label = dev.model.label or dev.model.id
            pin = dev.pins.get(pin_id)
            pin_label = pin.model.label if pin and pin.model.label else pin_id
            return f"{html.escape(dev_label)} ({html.escape(dev.model.id)}) / {html.escape(pin_label)} ({html.escape(pin_id)})"

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

    def update_geometry(self, rebuild_handles: bool = True):
        nodes = self._build_nodes()
        if len(nodes) < 2:
            return

        path = QPainterPath(nodes[0])
        for pt in nodes[1:]:
            path.lineTo(pt)
        self.setPath(path)
        self.halo_path.setPath(path)
        self._update_twist_path(nodes)

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
            handle.setPos(x, y)
            self.elbow_handles.append(handle)

        # segments
        for i in range(len(nodes) - 1):
            p1, p2 = nodes[i], nodes[i+1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            handle = SegmentHandle(self, i, p1, p2)
            handle.setParentItem(self)
            handle.setPos(mid)
            self.segment_handles.append(handle)

    def _update_handle_positions(self, nodes):
        # Update existing handles after a drag without recreating/removing the one under the cursor.
        for idx, handle in enumerate(self.elbow_handles):
            if idx < len(self.model.route):
                x, y = self.model.route[idx]
                handle.setPos(x, y)

        if len(self.segment_handles) != len(nodes) - 1:
            # topology changed; rebuild fully
            self._rebuild_handles(nodes)
            return

        for i, handle in enumerate(self.segment_handles):
            p1, p2 = nodes[i], nodes[i+1]
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            handle.setPos(mid)

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

    def _offset_nodes_for_twist(self, nodes, offset=4.0):
        if len(nodes) < 2:
            return nodes
        out = []
        sign = 1.0
        for i, p in enumerate(nodes):
            if i == 0:
                n = self._segment_normal(nodes[0], nodes[1])
            elif i == len(nodes) - 1:
                n = self._segment_normal(nodes[-2], nodes[-1])
            else:
                n1 = self._segment_normal(nodes[i-1], nodes[i])
                n2 = self._segment_normal(nodes[i], nodes[i+1])
                n = QPointF(n1.x() + n2.x(), n1.y() + n2.y())
                length = math.hypot(n.x(), n.y())
                if length != 0:
                    n = QPointF(n.x() / length, n.y() / length)
                else:
                    n = n1
            out.append(QPointF(p.x() + n.x() * offset * sign, p.y() + n.y() * offset * sign))
            sign *= -1.0
        return out

    def _update_twist_path(self, nodes):
        if not self.model.twisted:
            self.twist_path.hide()
            return
        offset_nodes = self._offset_nodes_for_twist(nodes, offset=4.0)
        if len(offset_nodes) < 2:
            self.twist_path.hide()
            return
        path = QPainterPath(offset_nodes[0])
        for pt in offset_nodes[1:]:
            path.lineTo(pt)
        self.twist_path.setPath(path)
        self.twist_path.show()

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

    def move_segment_handle(self, segment_index: int, new_mid: QPointF, anchor_mid: QPointF):
        nodes = self._build_nodes()
        if segment_index < 0 or segment_index >= len(nodes) - 1:
            return
        new_mid = self._snap_point(new_mid)
        delta = new_mid - anchor_mid
        if delta.isNull():
            return
        start_is_pin = segment_index == 0
        end_is_pin = segment_index + 1 == len(nodes) - 1

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

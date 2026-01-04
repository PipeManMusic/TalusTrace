import sys
import uuid
import yaml
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QLabel,
    QFileDialog,
    QMenu,
    QGraphicsItemGroup,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox
from talustrace.frontend.canvas import HarnessScene, HarnessView
from talustrace.frontend.items import DeviceItem, WireItem, TwistNodeItem, TwistedBundleItem
from talustrace.backend.models import Device, Wire, Harness

class MainWindow(QMainWindow):
    def __init__(self, autosave_dir: Path | None = None, restore_policy: str = "prompt"):
        super().__init__()
        self.setWindowTitle("Talus Trace - Harness CAD")
        self.resize(1200, 800)

        # UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        
        self.act_add_dev = QAction("Add Device", self)
        self.act_add_dev.triggered.connect(self.mode_add_device)
        self.toolbar.addAction(self.act_add_dev)

        self.act_add_bundle = QAction("Add Bundle", self)
        self.act_add_bundle.triggered.connect(self.mode_add_bundle)
        self.toolbar.addAction(self.act_add_bundle)

        # Menus
        self.recent_files = []
        self.recent_menu = None
        self._build_menus()

        # Status Bar
        self.status = QLabel("Ready")
        self.statusBar().addWidget(self.status)

        # Canvas
        self.scene = HarnessScene()
        self.view = HarnessView(self.scene)
        self.layout.addWidget(self.view)

        # Signals
        self.view.canvas_clicked.connect(self.handle_canvas_click)
        self.view.wire_connected.connect(self.handle_wire_creation)

        # Init
        self.device_items = []
        self.wire_items = []
        self.twist_nodes = []
        self.bundle_items = []
        self.current_path = None
        self.dirty = False
        self.mark_clean()
        
        # Autosave/restore
        self.autosave_dir = autosave_dir or (Path.cwd() / "autosaves")
        self.autosave_dir.mkdir(parents=True, exist_ok=True)
        self.restore_policy = restore_policy  # prompt | auto | skip
        self._setup_autosave_timer()
        self._maybe_restore_autosave()

    def mode_select(self):
        self.view.stop_ghost()
        self.status.setText("Select Mode")

    def mode_add_device(self):
        dummy_model = Device(id="ghost", label="New Device", pins=0)
        ghost = DeviceItem(dummy_model, on_changed=self.mark_dirty, on_delete_device=None, on_delete_pin=None)
        self.view.start_ghost(ghost, mode="PLACE_DEVICE")
        self.status.setText("Place Mode: Click to drop device. Esc to cancel.")

    def mode_add_bundle(self):
        ghost_group = self._build_bundle_group()
        self.view.start_ghost(ghost_group, mode="PLACE_BUNDLE")
        self.status.setText("Place Mode: Click to drop twisted bundle. Esc to cancel.")

    def handle_canvas_click(self, x, y):
        if self.view.mode == "PLACE_DEVICE":
            self.add_device(x, y)
            self.mark_dirty()
        elif self.view.mode == "PLACE_BUNDLE":
            self.add_twisted_bundle(x, y)
            self.mark_dirty()

    def handle_wire_creation(self, start_pin_item, end_pin_item):
        """Called when user successfully connects two pins."""
        # 1. Get Device and Pin IDs
        dev_start = start_pin_item.parentItem()
        dev_end = end_pin_item.parentItem()
        
        start_id = f"{dev_start.model.id}.{start_pin_item.model.id}"
        end_id = f"{dev_end.model.id}.{end_pin_item.model.id}"

        # Merge metadata from devices and pins (end overrides start on key conflict)
        start_dev_meta = getattr(dev_start.model, "meta", {}) or {}
        end_dev_meta = getattr(dev_end.model, "meta", {}) or {}
        start_meta = getattr(start_pin_item.model, "meta", {}) or {}
        end_meta = getattr(end_pin_item.model, "meta", {}) or {}
        merged_meta = {**start_dev_meta, **end_dev_meta, **start_meta, **end_meta}
        
        # 2. Create Data Model
        wire_id = str(uuid.uuid4())[:8]
        wire_data = Wire(id=wire_id, from_conn=start_id, to_conn=end_id, color="RD", meta=merged_meta)
        
        # 3. Create Visual Wire
        # Pass the DeviceItem objects so the wire can track movement
        wire_item = WireItem(wire_data, source_item=dev_start, target_item=dev_end, on_changed=self.mark_dirty, on_delete=self._delete_wire_item)
        self.scene.addItem(wire_item)
        self.wire_items.append(wire_item)
        self.mark_dirty()
        
        self.status.setText(f"Connected Wire: {start_id} -> {end_id}")

    def add_device(self, x, y, label="New Device", pins=0, mark_dirty=True):
        unique_id = str(uuid.uuid4())[:8]
        dev = Device(id=unique_id, label=label, pins=pins, x=x, y=y)
        item = DeviceItem(dev, on_changed=self.mark_dirty, on_delete_device=self._delete_device_item, on_delete_pin=self._delete_pin_item)
        self.scene.addItem(item)
        self.device_items.append(item)
        if mark_dirty:
            self.mark_dirty()
        return item

    def add_twisted_bundle(self, x, y, spacing=200):
        node_a = TwistNodeItem(on_changed=self.mark_dirty)
        node_b = TwistNodeItem(on_changed=self.mark_dirty)
        node_a.setPos(x, y)
        node_b.setPos(x + spacing, y)

        bundle = TwistedBundleItem(node_a, node_b, on_changed=self.mark_dirty)
        bundle.update_geometry()

        self.scene.addItem(node_a)
        self.scene.addItem(node_b)
        self.scene.addItem(bundle)

        self.twist_nodes.extend([node_a, node_b])
        self.bundle_items.append(bundle)

        return bundle

    def _build_bundle_group(self, spacing=200):
        node_a = TwistNodeItem(on_changed=None)
        node_b = TwistNodeItem(on_changed=None)
        node_b.setPos(spacing, 0)
        bundle = TwistedBundleItem(node_a, node_b, on_changed=None)
        bundle.update_geometry()

        group = QGraphicsItemGroup()
        node_a.setParentItem(group)
        node_b.setParentItem(group)
        bundle.setParentItem(group)
        return group

    def save_file(self):
        if not self.current_path:
            return self.save_file_as()
        self.save_harness(self.current_path)

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Harness", "", "YAML Files (*.yaml)")
        if not path:
            return
        final_path = self._ensure_yaml_suffix(path)
        self.save_harness(final_path)

    def load_file(self):
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load Harness", "", "YAML Files (*.yaml)")
        if not path:
            return
        self.load_harness(path)

    def _build_harness_model(self):
        devices = []
        wires = []

        for item in self.scene.items():
            if isinstance(item, DeviceItem):
                devices.append(item.model)
            elif isinstance(item, WireItem):
                wires.append(item.model)

        return Harness(devices=devices, wires=wires)

    def save_harness(self, path):
        harness = self._build_harness_model()

        with open(path, 'w') as f:
            yaml.dump(harness.model_dump(mode='json'), f, sort_keys=False)

        self.current_path = path
        self.mark_clean()
        self.add_recent_file(path)
        self.status.setText(f"Saved to {path}")
        self.current_path = Path(path)

    def autosave_snapshot(self, path=None):
        if not path:
            path = self.autosave_dir / "autosave.yaml"
        harness = self._build_harness_model()
        with open(path, 'w') as f:
            yaml.dump(harness.model_dump(mode='json'), f, sort_keys=False)
        self.status.setText(f"Autosaved to {path}")

    def _ensure_yaml_suffix(self, path: str | Path) -> Path:
        p = Path(path)
        if p.suffix.lower() in {".yaml", ".yml"}:
            return p
        return p.with_suffix(".yaml")

    def load_harness(self, path, set_current=True, record_recent=True):
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        harness = Harness(**data)

        self.scene.clear()
        self.device_items.clear()
        self.wire_items.clear()
        self.twist_nodes.clear()
        self.bundle_items.clear()

        device_map = {}  # ID -> DeviceItem

        for dev_model in harness.devices:
            item = DeviceItem(dev_model, on_changed=self.mark_dirty, on_delete_device=self._delete_device_item, on_delete_pin=self._delete_pin_item)
            self.scene.addItem(item)
            self.device_items.append(item)
            device_map[dev_model.id] = item

        for wire_model in harness.wires:
            src_dev_id = wire_model.from_conn.split('.')[0]
            tgt_dev_id = wire_model.to_conn.split('.')[0]

            src_item = device_map.get(src_dev_id)
            tgt_item = device_map.get(tgt_dev_id)

            if src_item and tgt_item:
                wire_item = WireItem(wire_model, source_item=src_item, target_item=tgt_item, on_changed=self.mark_dirty, on_delete=self._delete_wire_item)
                self.scene.addItem(wire_item)
                self.wire_items.append(wire_item)

        if set_current:
            self.current_path = Path(path)
        else:
            self.current_path = None
        self.mark_clean()
        if record_recent and set_current:
            self.add_recent_file(path)
        self.status.setText(f"Loaded from {path}")

    def new_file(self):
        if not self._confirm_discard_changes():
            return
        self.scene.clear()
        self.device_items.clear()
        self.wire_items.clear()
        self.twist_nodes.clear()
        self.bundle_items.clear()
        self.current_path = None
        self.mark_clean()
        self.status.setText("New harness")

    def closeEvent(self, event):
        if not self._confirm_discard_changes():
            event.ignore()
            return
        super().closeEvent(event)

    # --- Menus and helpers ---
    def _build_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        act_new = QAction("New", self)
        act_new.triggered.connect(self.new_file)
        file_menu.addAction(act_new)

        act_open = QAction("Open...", self)
        act_open.triggered.connect(self.load_file)
        file_menu.addAction(act_open)

        act_save = QAction("Save", self)
        act_save.triggered.connect(self.save_file)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save As...", self)
        act_save_as.triggered.connect(self.save_file_as)
        file_menu.addAction(act_save_as)

        self.recent_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_menu)
        self._rebuild_recent_menu()

        file_menu.addSeparator()
        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

    def _rebuild_recent_menu(self):
        if not self.recent_menu:
            return
        self.recent_menu.clear()
        if not self.recent_files:
            dummy = QAction("(Empty)", self)
            dummy.setEnabled(False)
            self.recent_menu.addAction(dummy)
            return
        for path in self.recent_files:
            act = QAction(str(path), self)
            act.triggered.connect(lambda checked=False, p=path: self._load_recent(p))
            self.recent_menu.addAction(act)

    def _load_recent(self, path):
        if not self._confirm_discard_changes():
            return
        self.load_harness(path)

    def _confirm_discard_changes(self):
        if not self.dirty:
            return True
        # In headless/test flows where restore_policy="skip", skip the dialog and discard.
        if self.restore_policy == "skip":
            return True
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("You have unsaved changes. Save before continuing?")
        save_btn = msg.addButton(QMessageBox.Save)
        discard_btn = msg.addButton("Discard", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton(QMessageBox.Cancel)
        msg.setDefaultButton(save_btn)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked is save_btn:
            self.save_file()
            return not self.dirty
        if clicked is discard_btn:
            return True
        # In headless/test contexts clicked may be None; treat that as cancel = discard
        if clicked is None:
            return True
        return False

    def mark_dirty(self):
        self.dirty = True

    def mark_clean(self):
        self.dirty = False

    def add_recent_file(self, path):
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:5]
        self._rebuild_recent_menu()

    # --- Autosave/restore helpers ---
    def _setup_autosave_timer(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(60000)  # 60s
        self.autosave_timer.timeout.connect(self._maybe_autosave)
        self.autosave_timer.start()

    def _maybe_autosave(self):
        if self.dirty:
            self.autosave_snapshot()

    def _latest_autosave(self):
        if not self.autosave_dir.exists():
            return None
        candidates = sorted(self.autosave_dir.glob("*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None

    def _maybe_restore_autosave(self):
        if self.restore_policy == "skip":
            return
        latest = self._latest_autosave()
        if not latest:
            return
        if self.restore_policy == "auto":
            self.load_harness(latest, set_current=False, record_recent=False)
            self.status.setText(f"Restored autosave {latest}")
            return
        resp = QMessageBox.question(
            self,
            "Restore Session",
            f"Restore last autosave?\n{latest}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp == QMessageBox.Yes:
            self.load_harness(latest, set_current=False, record_recent=False)
            self.status.setText(f"Restored autosave {latest}")

    # --- Delete helpers ---
    def _delete_device_item(self, item: DeviceItem):
        if not item:
            return
        # Remove attached wires
        for wire in list(item.attached_wires):
            if wire in self.wire_items:
                self.wire_items.remove(wire)
            if wire.scene():
                wire.scene().removeItem(wire)
            if wire.source_dev and wire in wire.source_dev.attached_wires:
                wire.source_dev.attached_wires.remove(wire)
            if wire.target_dev and wire in wire.target_dev.attached_wires:
                wire.target_dev.attached_wires.remove(wire)

        if item in self.device_items:
            self.device_items.remove(item)
        if item.scene():
            item.scene().removeItem(item)
        self.mark_dirty()

    def _delete_pin_item(self, device_item: DeviceItem, pin_item):
        if not device_item or not pin_item:
            return
        # Remove wires attached to this pin
        for wire in list(device_item.attached_wires):
            if wire.src_pin_id == pin_item.model.id or wire.tgt_pin_id == pin_item.model.id:
                if wire in self.wire_items:
                    self.wire_items.remove(wire)
                if wire.scene():
                    wire.scene().removeItem(wire)
                if wire.source_dev and wire in wire.source_dev.attached_wires:
                    wire.source_dev.attached_wires.remove(wire)
                if wire.target_dev and wire in wire.target_dev.attached_wires:
                    wire.target_dev.attached_wires.remove(wire)

        # Remove the pin model
        device_item.model.pins = [p for p in device_item.model.pins if p is not pin_item.model]

        # Re-layout pins and attached wires
        device_item.layout_pins()
        self.mark_dirty()

    def _delete_wire_item(self, wire_item: WireItem):
        if not wire_item:
            return
        if wire_item in self.wire_items:
            self.wire_items.remove(wire_item)
        if wire_item.source_dev and wire_item in wire_item.source_dev.attached_wires:
            wire_item.source_dev.attached_wires.remove(wire_item)
        if wire_item.target_dev and wire_item in wire_item.target_dev.attached_wires:
            wire_item.target_dev.attached_wires.remove(wire_item)
        if wire_item.scene():
            wire_item.scene().removeItem(wire_item)
        self.mark_dirty()


def main():
    app = QApplication(sys.argv)
    # Dark tooltip frame to match wire tooltip HTML contents
    app.setStyleSheet(
        "QToolTip {"
        " background-color: #303030;"
        " color: #f5f5f5;"
        " border: 1px solid #272727;"
        " font-family: monospace;"
        " font-size: 11px;"
        " }"
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
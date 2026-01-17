from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QScrollArea
from core.device import Device, Pin
from core.wire import Wire
from api.manager import APIManager
from api.commands.edit import UpdatePropertyCommand

class PropertyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.header = QLabel("Properties")
        self.header.setStyleSheet("font-weight: bold; padding: 10px; background: #2c313a; color: white;")
        self.layout.addWidget(self.header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        from PySide6.QtWidgets import QSizePolicy
        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.form = QFormLayout(self.content)
        self.scroll.setWidget(self.content)
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)
        
        # Subscribe to Selection Changes
        self.api.subscribe("selection_changed", self.on_selection_changed)
        self.api.subscribe("model_changed", self.refresh)
        
        self.current_item = None
        self.refresh()

    def on_selection_changed(self, data):
        # Use the event payload for selection
        sel = data.get('selection', [])
        print(f"[PropertyPanel] on_selection_changed: selection={sel}")
        self.current_item = sel[0] if sel else None
        self.refresh()

    def refresh(self, data=None):
        print(f"[PropertyPanel] refresh: current_item={self.current_item}")
        # Clear existing rows
        while self.form.count():
            child = self.form.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if not self.current_item:
            print("[PropertyPanel] refresh: No Selection")
            self.form.addRow(QLabel("No Selection"))
            self.content.adjustSize()
            self.scroll.ensureVisible(0, 0, 1, 1)
            return
        model = self.current_item
        print(f"[PropertyPanel] refresh: model type={type(model).__name__}, model={model}")
        # Route to specific renderer
        if isinstance(model, Device):
            print("[PropertyPanel] refresh: rendering Device")
            self._render_device(model)
        elif isinstance(model, Wire):
            print("[PropertyPanel] refresh: rendering Wire")
            self._render_wire(model)
        elif isinstance(model, Pin):
            print("[PropertyPanel] refresh: rendering Pin")
            self._render_pin(model) # <--- NEW HANDLER
        else:
            print(f"[PropertyPanel] refresh: Unknown Item: {type(model).__name__}")
            self.form.addRow(QLabel(f"Unknown Item: {type(model).__name__}"))

    def _render_device(self, device):
        self._add_field("ID", device.id, read_only=True)
        self._add_field("Label", device.label, lambda v: self._update_model(device, "label", v))
        self._add_field("Type", device.type)
        self._add_field("Library ID", device.library_id)

    def _render_wire(self, wire):
        self._add_field("ID", wire.id, read_only=True)
        self._add_field("From", f"{wire.from_conn}:{wire.from_pin}", read_only=True)
        self._add_field("To", f"{wire.to_conn}:{wire.to_pin}", read_only=True)
        self._add_field("Color", wire.color, lambda v: self._update_model(wire, "color", v))
        self._add_field("Gauge", str(wire.gauge), lambda v: self._update_model(wire, "gauge", v))

    def _render_pin(self, pin):
        # --- NEW PIN RENDERER ---
        self._add_field("Pin ID", pin.id, read_only=True)
        self._add_field("Signal", pin.signal, lambda v: self._update_model(pin, "signal", v))
        
        # Calculate Absolute Position for reference
        self.form.addRow(QLabel("--- Geometry ---"))
        self._add_field("Rel X", str(pin.x), lambda v: self._update_model(pin, "x", float(v)))
        self._add_field("Rel Y", str(pin.y), lambda v: self._update_model(pin, "y", float(v)))

    def _add_field(self, label, value, callback=None, read_only=False):
        lbl = QLabel(label)
        edit = QLineEdit(str(value) if value is not None else "")
        if read_only:
            edit.setReadOnly(True)
            edit.setStyleSheet("color: gray;")
        elif callback:
            edit.editingFinished.connect(lambda: callback(edit.text()))
        
        self.form.addRow(lbl, edit)

    def _update_model(self, item, field, value):
        # Use Command Pattern
        cmd = UpdatePropertyCommand(item, field, value)
        self.api.context.undo_stack.push(cmd)
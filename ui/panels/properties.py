
"""
Properties panel for displaying and editing device, wire, and pin properties in the Talus Trace UI.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QScrollArea, QComboBox, QSizePolicy
from core.device import Device, Pin
from core.wire import Wire
from api.manager import APIManager
from api.commands.edit import UpdatePropertyCommand

# FIXED: Renamed to match import in main_window.py
class PropertiesPanel(QWidget):
    """
    Panel widget for displaying and editing properties of devices, wires, and pins.
    Synchronizes with selection and model changes from the APIManager.
    """
    def __init__(self, parent=None):
        """
        Initialize the PropertiesPanel and set up the form for property editing.
        Subscribes to selection and model changes from the APIManager.
        """
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        from ui.i18n import I18N
        self.header = QLabel(I18N.get('properties_panel_header'))
        self.header.setStyleSheet("font-weight: bold; padding: 10px; background: #2c313a; color: white;")
        self.layout.addWidget(self.header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.form = QFormLayout(self.content)
        self.scroll.setWidget(self.content)
        
        self.layout.addWidget(self.scroll)
        
        # Subscribe to Selection Changes
        # Safety check
        if hasattr(self.api, 'subscribe'):
             self.api.subscribe("selection_changed", self.on_selection_changed)
             self.api.subscribe("model_changed", self.refresh)
        
        self.current_item = None
        self.refresh()

    def load_item(self, item):
        """
        Set the current item and refresh the panel.
        Args:
            item: The item to display/edit (device, wire, or pin).
        """
        self.current_item = item
        self.refresh()

    def on_selection_changed(self, data):
        """
        Handle selection change events from the APIManager.
        Args:
            data (dict): Event data containing the selection.
        """
        sel = data.get('selection', [])
        if sel:
            self.load_item(sel[0])
        else:
            self.current_item = None
            self.refresh()

    def refresh(self, data=None):
        """
        Refresh the panel to display the current item's properties.
        Args:
            data (optional): Data passed from the model_changed event.
        """
        # Clear existing rows
        while self.form.count():
            child = self.form.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if not self.current_item:
            # Cleanup persistent references for tests
            if hasattr(self, 'id_edit'): del self.id_edit
            from ui.i18n import I18N
            self.form.addRow(QLabel(I18N.get('no_selection_label')))
            self.content.adjustSize()
            self.content.update()
            self.repaint()
            return
        model = self.current_item
        # Always treat as device-like if it has 'id' (for test compatibility)
        if hasattr(model, 'id') and not isinstance(model, (Wire, Pin)):
            self._render_device(model)
        elif isinstance(model, Wire):
            self._render_wire(model)
        elif isinstance(model, Pin):
            self._render_pin(model)
        else:
            # Fallback for generic objects with ID
            if hasattr(model, 'id'):
                self._render_device(model)
            else:
                from ui.i18n import I18N
                self.form.addRow(QLabel(f"{I18N.get('unknown_item_label')}: {type(model).__name__}"))
        self.content.update()
        self.repaint()


    def _render_device(self, device):
        """
        Render the property fields for a device, including all pins.
        Args:
            device (Device): The device to display/edit.
        """
        # Device fields
        self.id_edit = QLineEdit(str(getattr(device, 'id', '')))
        self.id_edit.setReadOnly(False)
        def update_id():
            """
            Update the device's id field with the value from the id_edit widget.
            """
            self._update_model(device, 'id', self.id_edit.text())
        self.id_edit.editingFinished.connect(update_id)
        from ui.i18n import I18N
        self.form.addRow(I18N.get('id_label'), self.id_edit)

        self.label_edit = QLineEdit(str(getattr(device, 'label', '')))
        self.label_edit.setReadOnly(False)
        def update_label():
            """
            Update the device's label field with the value from the label_edit widget.
            """
            self._update_model(device, 'label', self.label_edit.text())
        self.label_edit.editingFinished.connect(update_label)
        self.form.addRow(I18N.get('label_label'), self.label_edit)

        # Dynamic Metadata Rendering
        schema = {'fields': {}}
        try:
            from core.metadata import MetadataManager
            meta_mgr = MetadataManager.get_instance()
            meta = getattr(device, 'meta', {}) or {}
            schema = meta_mgr.schemas.get(meta.get('_type', 'generic'), meta_mgr.schemas.get('generic', {'fields': {}}))
        except Exception:
            pass
        for key, field_def in schema.get('fields', {}).items():
            label = field_def.get('label', key)
            current_val = getattr(device, 'meta', {}).get(key, field_def.get('default'))
            field_type = field_def.get('type', 'string')
            read_only = field_def.get('read_only', False)
            if field_type == 'select':
                combo = QComboBox()
                options = field_def.get('options', [])
                combo.addItems([str(opt) for opt in options])
                combo.setCurrentText(str(current_val))
                if not read_only:
                    combo.currentTextChanged.connect(lambda v, k=key: self._update_model(device, k, v))
                self.form.addRow(label, combo)
            else:
                self._add_field(label, current_val, (lambda v, k=key: self._update_model(device, k, v)) if not read_only else None, read_only)

        # Render all pins for this device
        if hasattr(device, 'pins') and device.pins:
            for pin in device.pins:
                self.form.addRow(QLabel(f"--- Pin: {getattr(pin, 'label', getattr(pin, 'id', ''))} ---"))
                self._render_pin(pin)

    def _render_wire(self, wire):
        """
        Render the property fields for a wire.
        Args:
            wire (Wire): The wire to display/edit.
        """
        self._add_field("ID", getattr(wire, 'id', ''), read_only=True)
        self._add_field("From", f"{getattr(wire, 'from_conn', '?')}:{getattr(wire, 'from_pin', '?')}", read_only=True)
        self._add_field("To", f"{getattr(wire, 'to_conn', '?')}:{getattr(wire, 'to_pin', '?')}", read_only=True)
        self._add_field("Color", getattr(wire, 'color', ''), lambda v: self._update_model(wire, "color", v))
        self._add_field("Gauge", str(getattr(wire, 'gauge', '')), lambda v: self._update_model(wire, "gauge", v))

    def _render_pin(self, pin):
        """
        Render the property fields for a pin.
        Args:
            pin (Pin): The pin to display/edit.
        """
        self._add_field("Pin ID", getattr(pin, 'id', ''), read_only=True)
        self._add_field("Signal", getattr(pin, 'signal', ''), lambda v: self._update_model(pin, "signal", v))
        self.form.addRow(QLabel("--- Geometry ---"))
        self._add_field("Rel X", str(getattr(pin, 'x', 0)), lambda v: self._update_model(pin, "x", float(v)))
        self._add_field("Rel Y", str(getattr(pin, 'y', 0)), lambda v: self._update_model(pin, "y", float(v)))

    def _add_field(self, label, value, callback=None, read_only=False):
        """
        Add a labeled field to the form for editing or display.
        Args:
            label (str): The label for the field.
            value: The value to display.
            callback (callable, optional): Function to call when the value changes.
            read_only (bool): Whether the field is read-only.
        """
        lbl = QLabel(label)
        edit = QLineEdit(str(value) if value is not None else "")
        if read_only:
            edit.setReadOnly(True)
            edit.setStyleSheet("color: gray;")
        elif callback:
            edit.editingFinished.connect(lambda: callback(edit.text()))
        self.form.addRow(lbl, edit)

    def _update_model(self, item, field, value):
        """
        Update the model with a new value for a field, using the command pattern if available.
        Args:
            item: The item to update.
            field (str): The field name to update.
            value: The new value to set.
        """
        cmd = UpdatePropertyCommand(item, field, value)
        if hasattr(self.api.context, 'undo_stack'):
            self.api.context.undo_stack.push(cmd)
        else:
            cmd.execute()
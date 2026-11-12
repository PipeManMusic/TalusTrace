
"""
Properties panel for displaying and editing device, wire, and pin properties in the Talus Trace UI.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QScrollArea, QComboBox, QSizePolicy, QPushButton, QColorDialog,
)
from PySide6.QtGui import QColor
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
        self.header.setStyleSheet("font-weight: bold; padding: 10px; background: #2d2d2d; color: #e0e0e0;")
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
            data (dict): Event data containing the selection and (optionally) device_dict.
        """
        sel = data.get('selection', [])
        device_dict = data.get('device_dict')
        if device_dict:
            # Use device_dict to reconstruct a Device with all pins and metadata
            from core.device import Device
            self.current_item = Device.from_dict(device_dict)
            self.refresh()
        elif sel:
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
        # Re-resolve current_item from the harness so we always render
        # the live model (not a stale copy from selection time).
        if self.current_item and hasattr(self.current_item, 'id'):
            item_id = self.current_item.id
            harness = self.api.context.harness
            live = None
            for dev in getattr(harness, 'devices', []):
                if getattr(dev, 'id', None) == item_id:
                    live = dev
                    break
                for pin in getattr(dev, 'pins', []):
                    if getattr(pin, 'id', None) == item_id:
                        live = pin
                        break
                if live is not None:
                    break
            if live is None:
                for w in getattr(harness, 'wires', []):
                    if getattr(w, 'id', None) == item_id:
                        live = w
                        break
            if live is not None:
                self.current_item = live
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
            self._render_pin(model, standalone=True)
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
        self.id_edit.setReadOnly(True)
        self.id_edit.setStyleSheet("color: gray;")
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

        # Always display all meta fields, even if not present in schema
        meta = getattr(device, 'meta', {}) or {}
        # Always fetch the latest schema from MetadataManager at render time
        schema_fields = {}
        try:
            from core.metadata import MetadataManager
            meta_mgr = MetadataManager.get_instance()
            # Always re-fetch schemas at render time
            schema = meta_mgr.schemas.get(meta.get('_type', 'generic'), meta_mgr.schemas.get('generic', {'fields': {}}))
            schema_fields = schema.get('fields', {})
        except Exception:
            pass
        # Render schema-defined fields in schema order
        rendered_keys = set()
        for key in schema_fields:
            field_def = schema_fields.get(key, {})
            label = field_def.get('label', key)
            field_type = field_def.get('type', 'string')
            read_only = field_def.get('read_only', False)
            current_val = meta.get(key, field_def.get('default', ''))
            meta_field = f"meta.{key}"
            rendered_keys.add(key)
            if field_type == 'select':
                combo = QComboBox()
                options = field_def.get('options', [])
                combo.addItems([str(opt) for opt in options])
                combo.setCurrentText(str(current_val))
                if not read_only:
                    def on_combo_change(v, k=meta_field):
                        """Callback for combo box value change. Updates the device model via API."""
                        self._update_model(device, k, v)
                    combo.currentTextChanged.connect(on_combo_change)
                self.form.addRow(label, combo)
            else:
                # Add type-aware validator and conversion for float/int fields
                if field_type == 'float':
                    validator = self._is_float
                    def make_callback(k):
                        """Return a callback that updates the device meta field as float via API."""
                        return lambda v: self._update_model(device, f"meta.{k}", float(v))
                elif field_type == 'int':
                    validator = lambda v: v.isdigit()
                    def make_callback(k):
                        """Return a callback that updates the device meta field as int via API."""
                        return lambda v: self._update_model(device, f"meta.{k}", int(v))
                else:
                    validator = None
                    def make_callback(k):
                        """Return a callback that updates the device meta field as string via API."""
                        return lambda v: self._update_model(device, f"meta.{k}", v)
                self._add_field(label, current_val, make_callback(key) if not read_only else None, read_only, validator)
        # Render extra meta fields not in schema, sorted alphabetically
        extra_keys = sorted(set(meta.keys()) - rendered_keys)
        for key in extra_keys:
            current_val = meta.get(key, '')
            meta_field = f"meta.{key}"
            def make_callback(k):
                """Return a callback that updates the device meta field via API."""
                return lambda v: self._update_model(device, f"meta.{k}", v)
            self._add_field(key, current_val, make_callback(key), False)

        # Render all pins for this device
        if hasattr(device, 'pins') and device.pins:
            for pin in device.pins:
                self.form.addRow(QLabel(f"--- Pin: {getattr(pin, 'label', getattr(pin, 'id', ''))} ---"))
                self._render_pin(pin)

    def _resolve_conn_label(self, device_uuid, pin_uuid):
        """Resolve device and pin UUIDs to a 'Device > Pin' label."""
        harness = getattr(self.api.context, 'harness', None)
        if not harness:
            return f"{device_uuid}:{pin_uuid}"
        dev_label = device_uuid
        pin_label = pin_uuid
        for dev in getattr(harness, 'devices', []):
            if getattr(dev, 'id', None) == device_uuid:
                dev_label = getattr(dev, 'label', None) or device_uuid
                for pin in getattr(dev, 'pins', []):
                    if getattr(pin, 'id', None) == pin_uuid:
                        pin_label = getattr(pin, 'label', None) or pin_uuid
                        break
                break
        return f"{dev_label} > {pin_label}"

    def _render_wire(self, wire):
        """
        Render the property fields for a wire.
        Args:
            wire (Wire): The wire to display/edit.
        """
        self._add_field("ID", getattr(wire, 'id', ''), read_only=True)
        from_label = self._resolve_conn_label(getattr(wire, 'from_conn', '?'), getattr(wire, 'from_pin', '?'))
        to_label = self._resolve_conn_label(getattr(wire, 'to_conn', '?'), getattr(wire, 'to_pin', '?'))
        self._add_field("From", from_label, read_only=True)
        self._add_field("To", to_label, read_only=True)

        # Wire spec selector — populated from wire library
        status = getattr(wire, 'status', 'UNDEFINED')
        self._add_field("Status", status, read_only=True)

        wire_lib = self.api.library.get_wires() if hasattr(self.api, 'library') else {}
        combo = QComboBox()
        combo.addItem("— Unspecified —", "")
        for spec_id, spec in wire_lib.items():
            combo.addItem(spec.get('label', spec_id), spec_id)

        # Pre-select current spec
        current_std = getattr(wire, 'standard_id', None) or ""
        idx = combo.findData(current_std)
        if idx >= 0:
            combo.setCurrentIndex(idx)

        def on_spec_selected(index):
            """Apply the selected wire spec from the library to this wire."""
            spec_id = combo.itemData(index)
            if not spec_id:
                return
            spec = wire_lib.get(spec_id, {})
            spec_color_code = spec.get('color_code', '')
            spec_color_hex = spec.get('color_hex', '')
            wire.promote_to_specified(
                standard_id=spec_id,
                gauge=spec.get('gauge', ''),
                color_code=spec_color_code,
                diameter_mm=spec.get('od_mm', 1.0),
            )
            # Apply DIN standard color to the wire's render color via API
            if spec_color_hex:
                self._update_model(wire, "color", spec_color_hex)
            self.api.dispatch("model_changed", {"action": "update", "item": wire})
            self.refresh()

        combo.activated.connect(on_spec_selected)
        self.form.addRow(QLabel("Wire Spec"), combo)

        # Show resolved spec details (read-only)
        self._add_field("Gauge", str(getattr(wire, 'gauge', '') or ''), read_only=True)
        self._add_field("Diameter (mm)", str(getattr(wire, 'diameter_mm', 1.0)), read_only=True)
        color_code = getattr(wire, 'color_code', '') or ''
        if color_code:
            self._add_field("DIN Color", color_code.upper(), read_only=True)

        # Color override — user can change after spec sets the default.
        # Clearing the hex field reverts to the DIN spec color.
        def apply_color(v):
            """Apply color override, or revert to DIN spec color if cleared."""
            if not v.strip():
                std = getattr(wire, 'standard_id', None)
                if std and std in wire_lib:
                    v = wire_lib[std].get('color_hex', '')
            self._update_model(wire, "color", v)
        self._add_color_field("Color", getattr(wire, 'color', ''), apply_color)

        # Signal — auto-populated from source pin if empty, editable for label printing
        current_signal = getattr(wire, 'signal_name', '') or ''
        if not current_signal:
            current_signal = self._resolve_pin_signal(wire)
        def on_signal_changed(v):
            """Update the wire signal name for heat shrink label use."""
            self._update_model(wire, "signal_name", v)
        self._add_field("Signal", current_signal, on_signal_changed)

        # Length — computed from path_nodes, read-only
        length_mm = getattr(wire, 'calculated_length_mm', 0.0)
        self._add_field("Length (mm)", f"{length_mm:.1f}", read_only=True)

    def _resolve_pin_signal(self, wire):
        """Resolve the signal name from the source pin if the wire has no signal set."""
        harness = getattr(self.api.context, 'harness', None)
        if not harness:
            return ''
        from_pin_id = getattr(wire, 'from_pin', '')
        if not from_pin_id:
            return ''
        for dev in getattr(harness, 'devices', []):
            for pin in getattr(dev, 'pins', []):
                if getattr(pin, 'id', None) == from_pin_id:
                    return getattr(pin, 'signal', '') or ''
        return ''

    def _render_pin(self, pin, standalone=False):
        """
        Render the property fields for a pin.
        Args:
            pin (Pin): The pin to display/edit.
            standalone (bool): If True, show parent device context header.
        """
        if standalone:
            # Show parent device context
            device_id = getattr(pin, 'device_id', None)
            parent_label = device_id or 'Unknown'
            if device_id:
                harness = self.api.context.harness
                for dev in getattr(harness, 'devices', []):
                    if getattr(dev, 'id', None) == device_id:
                        parent_label = getattr(dev, 'label', None) or device_id
                        break
            self.form.addRow(QLabel(f"Device: {parent_label}"))
        self._add_field("Pin ID", getattr(pin, 'id', ''), read_only=True)
        self._add_field("Label", getattr(pin, 'label', ''), lambda v: self._update_model(pin, "label", v))
        self._add_field("Signal", getattr(pin, 'signal', ''), lambda v: self._update_model(pin, "signal", v))
        self.form.addRow(QLabel("--- Geometry ---"))
        self._add_field(
            "Rel X", f"{getattr(pin, 'x', 0):.4f}",
            lambda v: self._update_model(pin, "x", round(float(v), 4)),
            validator=self._is_float
        )
        self._add_field(
            "Rel Y", f"{getattr(pin, 'y', 0):.4f}",
            lambda v: self._update_model(pin, "y", round(float(v), 4)),
            validator=self._is_float
        )

    def _is_float(self, v):
        """
        Check if the given value can be converted to a float.
        Args:
            v: The value to check.
        Returns:
            bool: True if v can be converted to float, False otherwise.
        """
        try:
            float(v)
            return True
        except Exception:
            return False

    def _add_field(self, label, value, callback=None, read_only=False, validator=None):
        """
        Add a labeled field to the form for editing or display.
        Args:
            label (str): The label for the field.
            value: The value to display.
            callback (callable, optional): Function to call when the value changes.
            read_only (bool): Whether the field is read-only.
            validator (callable, optional): Function to validate the input value.
        """
        lbl = QLabel(label)
        edit = QLineEdit(str(value) if value is not None else "")
        if read_only:
            edit.setReadOnly(True)
            edit.setStyleSheet("color: gray;")
        elif callback:
            def validate_and_commit():
                """
                Validate the input and commit the value if valid, otherwise show error feedback.
                """
                text = edit.text()
                valid = True
                if validator:
                    valid = validator(text)
                if valid:
                    edit.setStyleSheet("")
                    callback(text)
                else:
                    edit.setStyleSheet("border: 2px solid red;")
            edit.editingFinished.connect(validate_and_commit)
            edit.textChanged.connect(lambda _: edit.setStyleSheet("") if (not validator or validator(edit.text())) else edit.setStyleSheet("border: 2px solid red;"))
        self.form.addRow(lbl, edit)

    def _add_color_field(self, label, value, callback):
        """
        Add a color picker field: a swatch button (opens QColorDialog) plus an
        editable hex field. Clearing the hex field commits an empty string so
        callers can revert to a default (e.g. DIN spec color).
        """
        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(4)

        swatch = QPushButton()
        swatch.setFixedWidth(36)
        swatch.setAutoFillBackground(True)

        edit = QLineEdit(str(value) if value is not None else "")
        edit.setPlaceholderText("#RRGGBB")

        def _update_swatch(hex_str):
            """Recolor the preview swatch to reflect ``hex_str``."""
            qc = QColor(hex_str) if hex_str else QColor()
            if not qc.isValid():
                swatch.setStyleSheet("background: transparent; border: 1px dashed #888;")
                swatch.setText("?")
            else:
                text_color = "black" if qc.lightness() > 128 else "white"
                swatch.setStyleSheet(
                    f"background-color: {qc.name()}; color: {text_color}; "
                    f"border: 1px solid #555;"
                )
                swatch.setText("")

        def _commit(hex_str):
            """Persist the edited color and refresh the swatch."""
            _update_swatch(hex_str)
            callback(hex_str)

        def _on_pick():
            """Open a QColorDialog seeded with the current field value."""
            initial = QColor(edit.text()) if edit.text() else QColor("#808080")
            if not initial.isValid():
                initial = QColor("#808080")
            picked = QColorDialog.getColor(initial, self, "Pick Wire Color")
            if picked.isValid():
                name = picked.name()
                edit.setText(name)
                _commit(name)

        def _on_editing_finished():
            """Validate the typed hex string and commit if parseable."""
            text = edit.text().strip()
            if not text:
                _commit("")
                return
            qc = QColor(text)
            if qc.isValid():
                edit.setStyleSheet("")
                _commit(qc.name())
            else:
                edit.setStyleSheet("border: 2px solid red;")

        swatch.clicked.connect(_on_pick)
        edit.editingFinished.connect(_on_editing_finished)
        _update_swatch(value or "")

        hbox.addWidget(swatch)
        hbox.addWidget(edit, 1)
        self.form.addRow(QLabel(label), container)

    def _update_model(self, item, field, value):
        """
        Request a property update via the API, enforcing MVC (no direct mutation or undo stack access).
        Args:
            item: The item to update.
            field (str): The field name to update.
            value: The new value to set.
        """
        # Use the API's property update mechanism (dispatch action or call method)
        self.api.update_property(item, field, value)
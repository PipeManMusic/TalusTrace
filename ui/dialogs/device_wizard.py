"""
Device wizard dialog for Talus Trace.

Implements the 3-stage workflow from
``docs/specs/talus_trace_spec_custom_devices.md``:

    STATE_IMPORT   -> metadata + optional SVG
    STATE_SCALE    -> calibrate px -> mm (scale_factor)
    STATE_PINNING  -> map pin head/tail coordinates

On Finish the resulting part definition is saved to
``resources/library/parts.yaml`` via :class:`core.library_manager.LibraryManager`.
It is NOT placed in the harness (that is a separate user action from the
Library panel once the device is saved).

The wizard can also be launched in *Promotion* mode by passing an existing
generic :class:`core.device.Device` as ``source_device``; its pins pre-populate
the pinning page.
"""

from __future__ import annotations

import os
import re
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QLineEdit,
    QLabel,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QWidget,
)

try:  # QSvgWidget is optional; degrade gracefully if PySide6-Qt-Svg is missing.
    from PySide6.QtSvgWidgets import QSvgWidget  # type: ignore
except Exception:  # pragma: no cover
    QSvgWidget = None  # type: ignore


# -- helpers -----------------------------------------------------------------

_PART_ID_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


def _i18n(key: str, default: Optional[str] = None, **kwargs) -> str:
    """Thin wrapper around ``ui.i18n.I18N.get`` so pages can be tested in isolation."""
    from ui.i18n import I18N

    return I18N.get(key, default if default is not None else key, **kwargs)


# -- Page 1: Metadata / Import ----------------------------------------------


class MetadataPage(QWizardPage):
    """Collects identity, categorisation and an optional SVG body."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the metadata form and register QWizard fields."""
        super().__init__(parent)
        self.setTitle(_i18n("device_wizard_page_metadata_title", "Identity & Import"))
        self.setSubTitle(
            _i18n(
                "device_wizard_page_metadata_subtitle",
                "Describe the device and (optionally) import an SVG body.",
            )
        )

        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("CONN-DT04-4P")
        self.name_input = QLineEdit(self)
        self.manufacturer_input = QLineEdit(self)
        self.part_number_input = QLineEdit(self)
        self.category_input = QLineEdit(self)
        self.category_input.setPlaceholderText("Connectors / Splices / Terminals / ...")
        self.description_input = QTextEdit(self)
        self.description_input.setFixedHeight(60)

        self.svg_path_input = QLineEdit(self)
        self.svg_path_input.setReadOnly(True)
        self.browse_svg_btn = QPushButton(_i18n("device_wizard_browse_svg", "Browse SVG..."), self)
        self.browse_svg_btn.clicked.connect(self._pick_svg)
        svg_row = QHBoxLayout()
        svg_row.addWidget(self.svg_path_input, 1)
        svg_row.addWidget(self.browse_svg_btn)

        form = QFormLayout()
        form.addRow(_i18n("device_wizard_id_label", "Part ID*:"), self.id_input)
        form.addRow(_i18n("device_name_label", "Device Name:") + "*", self.name_input)
        form.addRow(_i18n("device_wizard_manufacturer", "Manufacturer:"), self.manufacturer_input)
        form.addRow(_i18n("device_wizard_part_number", "Part Number:"), self.part_number_input)
        form.addRow(_i18n("device_wizard_category", "Category:"), self.category_input)
        form.addRow(_i18n("device_wizard_description", "Description:"), self.description_input)
        form.addRow(_i18n("device_wizard_svg", "SVG body (optional):"), svg_row)

        self.error_label = QLabel(self)
        self.error_label.setStyleSheet("color: #c33;")
        self.error_label.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)

        # Register fields so downstream pages can read them via self.field(...)
        self.registerField("part_id*", self.id_input)
        self.registerField("name*", self.name_input)
        self.registerField("manufacturer", self.manufacturer_input)
        self.registerField("part_number", self.part_number_input)
        self.registerField("category", self.category_input)
        self.registerField("svg_path", self.svg_path_input)

        self.id_input.textChanged.connect(self.completeChanged)
        self.name_input.textChanged.connect(self.completeChanged)

    # Qt override ----------------------------------------------------------
    def isComplete(self) -> bool:  # noqa: N802 (Qt name)
        """Return True when the required fields are present and valid."""
        pid = self.id_input.text().strip()
        name = self.name_input.text().strip()
        if not pid or not name:
            self.error_label.setVisible(False)
            return False
        if not _PART_ID_RE.match(pid):
            self.error_label.setText(
                _i18n(
                    "device_wizard_id_invalid",
                    "Part ID may only contain letters, digits, '-' and '_'.",
                )
            )
            self.error_label.setVisible(True)
            return False
        self.error_label.setVisible(False)
        return True

    def description_text(self) -> str:
        """Return the free-form description entered by the user."""
        return self.description_input.toPlainText().strip()

    # -- private -----------------------------------------------------------
    def _pick_svg(self) -> None:
        """Prompt the user to select an SVG file for the device body."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            _i18n("device_wizard_pick_svg", "Select SVG file"),
            "",
            "SVG files (*.svg);;All files (*)",
        )
        if path:
            self.svg_path_input.setText(path)


# -- Page 2: Scale -----------------------------------------------------------


class ScalePage(QWizardPage):
    """Calibrates the physical footprint (mm) so the device renders 1:1.

    The full spec allows click-to-calibrate on the SVG preview to compute a
    pixel->mm ``scale_factor`` from a known real-world distance. That
    interactive calibration is flagged TODO; this page currently captures the
    physical width/height in mm, from which ``scale_factor`` is derived once
    the SVG native size is known.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the scale/calibration form and preview placeholder."""
        super().__init__(parent)
        self.setTitle(_i18n("device_wizard_page_scale_title", "Scale & Calibration"))
        self.setSubTitle(
            _i18n(
                "device_wizard_page_scale_subtitle",
                "Set the physical footprint so the device renders 1:1 on the formboard.",
            )
        )

        self.width_mm = QDoubleSpinBox(self)
        self.width_mm.setRange(0.1, 10_000.0)
        self.width_mm.setSuffix(" mm")
        self.width_mm.setValue(25.0)
        self.height_mm = QDoubleSpinBox(self)
        self.height_mm.setRange(0.1, 10_000.0)
        self.height_mm.setSuffix(" mm")
        self.height_mm.setValue(15.0)

        form = QFormLayout()
        form.addRow(_i18n("device_wizard_width_mm", "Physical width:"), self.width_mm)
        form.addRow(_i18n("device_wizard_height_mm", "Physical height:"), self.height_mm)

        self.preview_holder = QVBoxLayout()
        self.preview_label = QLabel(
            _i18n("device_wizard_no_svg", "(no SVG imported — geometry only)"), self
        )
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_holder.addWidget(self.preview_label)

        self.calibration_hint = QLabel(
            _i18n(
                "device_wizard_calibration_hint",
                "TODO: click two points on the preview to calibrate px → mm.",
            ),
            self,
        )
        self.calibration_hint.setStyleSheet("color: #888; font-style: italic;")

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(self.preview_holder)
        layout.addWidget(self.calibration_hint)

        self._preview_widget: Optional[QWidget] = None

    # Qt override ----------------------------------------------------------
    def initializePage(self) -> None:  # noqa: N802
        """Refresh the SVG preview when the page becomes visible."""
        svg_path = (self.field("svg_path") or "").strip()
        self._rebuild_preview(svg_path)

    def _rebuild_preview(self, svg_path: str) -> None:
        """Render (or clear) the SVG preview at ``svg_path``."""
        if self._preview_widget is not None:
            self.preview_holder.removeWidget(self._preview_widget)
            self._preview_widget.deleteLater()
            self._preview_widget = None

        if not svg_path or not os.path.exists(svg_path):
            self.preview_label.setVisible(True)
            return

        self.preview_label.setVisible(False)
        widget: Optional[QWidget] = None
        if QSvgWidget is not None:
            try:
                widget = QSvgWidget(svg_path)
                widget.setFixedSize(QSize(280, 180))
            except Exception:
                widget = None
        if widget is None:
            pm = QPixmap(svg_path)
            if not pm.isNull():
                lbl = QLabel(self)
                lbl.setPixmap(pm.scaled(280, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                widget = lbl
        if widget is not None:
            self._preview_widget = widget
            self.preview_holder.addWidget(widget, alignment=Qt.AlignCenter)
        else:
            self.preview_label.setVisible(True)


# -- Page 3: Pinning ---------------------------------------------------------


_PIN_COLUMNS = ["id", "label", "signal", "x_mm", "y_mm", "head_x", "head_y", "tail_x", "tail_y"]


class PinningPage(QWizardPage):
    """Editable pin table with add/remove; supports pre-fill from a source device."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the pin table and add/remove controls."""
        super().__init__(parent)
        self.setTitle(_i18n("device_wizard_page_pinning_title", "Pin Mapping"))
        self.setSubTitle(
            _i18n(
                "device_wizard_page_pinning_subtitle",
                'Define each pin. "Head" is the grid-locked wiring point; '
                '"Tail" is the physical SVG exit point.',
            )
        )

        self.pin_count_spin = QSpinBox(self)
        self.pin_count_spin.setRange(0, 512)
        self.pin_count_spin.setValue(2)
        self.apply_count_btn = QPushButton(
            _i18n("device_wizard_resize_pins", "Resize pin list"), self
        )
        self.apply_count_btn.clicked.connect(self._resize_from_spin)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel(_i18n("device_wizard_pin_count", "Pin count:"), self))
        count_row.addWidget(self.pin_count_spin)
        count_row.addWidget(self.apply_count_btn)
        count_row.addStretch(1)

        self.table = QTableWidget(0, len(_PIN_COLUMNS), self)
        self.table.setHorizontalHeaderLabels(_PIN_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.add_btn = QPushButton(_i18n("device_wizard_add_pin", "Add Pin"), self)
        self.add_btn.clicked.connect(lambda: self._append_pin_row({}))
        self.remove_btn = QPushButton(_i18n("device_wizard_remove_pin", "Remove Selected"), self)
        self.remove_btn.clicked.connect(self._remove_selected)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        btn_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(count_row)
        layout.addWidget(self.table)
        layout.addLayout(btn_row)

    # -- public ------------------------------------------------------------
    def prefill_from_pins(self, pins: List[Any]) -> None:
        """Populate the table from Pin model instances (used for promotion)."""
        self.table.setRowCount(0)
        for i, pin in enumerate(pins or []):
            head = getattr(pin, "head", None) or [getattr(pin, "x", 0.0), getattr(pin, "y", 0.0)]
            tail = getattr(pin, "tail", None) or head
            self._append_pin_row(
                {
                    "id": getattr(pin, "id", "") or str(i + 1),
                    "label": getattr(pin, "label", "") or str(i + 1),
                    "signal": getattr(pin, "signal", "") or "",
                    "x_mm": getattr(pin, "x", 0.0),
                    "y_mm": getattr(pin, "y", 0.0),
                    "head_x": head[0] if head else 0.0,
                    "head_y": head[1] if head and len(head) > 1 else 0.0,
                    "tail_x": tail[0] if tail else 0.0,
                    "tail_y": tail[1] if tail and len(tail) > 1 else 0.0,
                }
            )
        self.pin_count_spin.setValue(self.table.rowCount())

    def prefill_from_pin_dicts(self, pins: List[Dict[str, Any]]) -> None:
        """Populate the table from saved parts.yaml pin dicts (used for editing).

        Saved pins use ``x``/``y`` plus ``head``/``tail`` coordinate pairs (see
        :meth:`DeviceWizard.build_part_data`); map them onto the table columns.
        """
        self.table.setRowCount(0)
        for i, pin in enumerate(pins or []):
            if not isinstance(pin, dict):
                continue
            head = pin.get("head") or [pin.get("x", 0.0), pin.get("y", 0.0)]
            tail = pin.get("tail") or head
            self._append_pin_row(
                {
                    "id": str(pin.get("id", "") or (i + 1)),
                    "label": str(pin.get("label", "") or (i + 1)),
                    "signal": str(pin.get("signal", "") or ""),
                    "x_mm": pin.get("x", 0.0),
                    "y_mm": pin.get("y", 0.0),
                    "head_x": head[0] if head else 0.0,
                    "head_y": head[1] if head and len(head) > 1 else 0.0,
                    "tail_x": tail[0] if tail else 0.0,
                    "tail_y": tail[1] if tail and len(tail) > 1 else 0.0,
                }
            )
        self.pin_count_spin.setValue(self.table.rowCount())

    def collect_pins(self) -> List[Dict[str, Any]]:
        """Serialize the table into a list of dicts suitable for parts.yaml."""
        out: List[Dict[str, Any]] = []
        for row in range(self.table.rowCount()):
            entry: Dict[str, Any] = {}
            for col, key in enumerate(_PIN_COLUMNS):
                item = self.table.item(row, col)
                text = item.text().strip() if item else ""
                if key in ("id", "label", "signal"):
                    entry[key] = text
                else:
                    try:
                        entry[key] = float(text) if text else 0.0
                    except ValueError:
                        entry[key] = 0.0
            if not entry.get("id"):
                entry["id"] = str(row + 1)
            if not entry.get("label"):
                entry["label"] = entry["id"]
            out.append(entry)
        return out

    # -- Qt overrides ------------------------------------------------------
    def initializePage(self) -> None:  # noqa: N802
        """Seed the table with a default row set when first shown."""
        if self.table.rowCount() == 0:
            for i in range(max(1, self.pin_count_spin.value())):
                self._append_pin_row({"id": str(i + 1), "label": str(i + 1)})

    # -- private -----------------------------------------------------------
    def _append_pin_row(self, values: Dict[str, Any]) -> None:
        """Append a new pin row, pre-filling any provided column values."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, key in enumerate(_PIN_COLUMNS):
            default = str(row + 1) if key in ("id", "label") else ""
            raw = values.get(key, default)
            self.table.setItem(row, col, QTableWidgetItem("" if raw is None else str(raw)))

    def _remove_selected(self) -> None:
        """Delete every row that has a selected cell."""
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
        self.pin_count_spin.setValue(self.table.rowCount())

    def _resize_from_spin(self) -> None:
        """Grow/shrink the pin table to match the pin-count spin box."""
        target = self.pin_count_spin.value()
        current = self.table.rowCount()
        if target > current:
            for i in range(current, target):
                self._append_pin_row({"id": str(i + 1), "label": str(i + 1)})
        elif target < current:
            for _ in range(current - target):
                self.table.removeRow(self.table.rowCount() - 1)


# -- Wizard orchestrator -----------------------------------------------------


class DeviceWizard(QWizard):
    """Multi-page wizard for creating (or promoting) a library device.

    Parameters
    ----------
    parent:
        Parent widget.
    source_device:
        Optional existing :class:`core.device.Device` (typically a "generic"
        device from the harness). When provided, metadata and pins are
        pre-populated to support the **Promotion** flow described in the spec.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        source_device: Any = None,
        edit_part_id: Optional[str] = None,
    ) -> None:
        """Create the wizard.

        Pass ``source_device`` to enable promotion pre-fill, or ``edit_part_id``
        to load an existing library part for editing (its metadata, scale, SVG
        and pins are pre-populated and the Part ID is locked).
        """
        super().__init__(parent)
        self.setWindowTitle(_i18n("device_wizard_title", "Device Wizard"))
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        self.setOption(QWizard.HaveHelpButton, False)

        self.source_device = source_device
        self.edit_part_id = edit_part_id
        # When editing an existing part we preserve its stored SVG body unless
        # the user browses to a new file (the saved SVG is a string, not a path).
        self._existing_svg_body: Optional[str] = None
        self.last_saved_part_id: Optional[str] = None
        self.last_saved_path: Optional[str] = None

        self.metadata_page = MetadataPage(self)
        self.scale_page = ScalePage(self)
        self.pinning_page = PinningPage(self)

        self.addPage(self.metadata_page)
        self.addPage(self.scale_page)
        self.addPage(self.pinning_page)

        if edit_part_id is not None:
            self._prefill_from_library_part(edit_part_id)
        elif source_device is not None:
            self._prefill_from_device(source_device)

    # -- public helpers ----------------------------------------------------
    def build_part_data(self) -> Dict[str, Any]:
        """Assemble the YAML-ready dict for ``parts.yaml``."""
        pins = self.pinning_page.collect_pins()
        data: Dict[str, Any] = {
            "manufacturer": self.metadata_page.manufacturer_input.text().strip(),
            "part_number": self.metadata_page.part_number_input.text().strip(),
            "category": self.metadata_page.category_input.text().strip(),
            "description": self.metadata_page.description_text(),
            "name": self.metadata_page.name_input.text().strip(),
            "width_mm": float(self.scale_page.width_mm.value()),
            "height_mm": float(self.scale_page.height_mm.value()),
            "pins": [
                {
                    "id": p["id"],
                    "label": p["label"],
                    "signal": p["signal"],
                    "x": p["x_mm"],
                    "y": p["y_mm"],
                    "head": [p["head_x"], p["head_y"]],
                    "tail": [p["tail_x"], p["tail_y"]],
                }
                for p in pins
            ],
        }
        svg_path = self.metadata_page.svg_path_input.text().strip()
        if svg_path and os.path.exists(svg_path):
            try:
                with open(svg_path, "r", encoding="utf-8") as f:
                    data["svg_body"] = f.read()
            except Exception:
                data["svg_body"] = None
        elif self._existing_svg_body:
            # Editing an existing part and no new SVG chosen: keep the stored one.
            data["svg_body"] = self._existing_svg_body
        if self.source_device is not None:
            data["promotion_source_id"] = getattr(self.source_device, "id", None)
        return data

    # -- Qt override -------------------------------------------------------
    def accept(self) -> None:  # noqa: D401
        """Save the assembled part to the library and close the dialog."""
        part_id = (self.field("part_id") or "").strip()
        if not part_id:
            QMessageBox.warning(
                self,
                _i18n("device_wizard_title", "Device Wizard"),
                _i18n("device_wizard_id_required", "A Part ID is required."),
            )
            return

        data = self.build_part_data()
        try:
            from core.library_manager import LibraryManager

            lm = LibraryManager()
            path = lm.save_part(part_id, data)
        except Exception as exc:  # pragma: no cover — surface any write failure
            QMessageBox.critical(
                self,
                _i18n("device_wizard_title", "Device Wizard"),
                _i18n(
                    "device_wizard_save_failed",
                    "Failed to save device to library:\n{err}",
                    err=str(exc),
                ),
            )
            return

        self.last_saved_part_id = part_id
        self.last_saved_path = path

        if self.source_device is not None:
            self._apply_saved_part_to_source_device(part_id, data)

        # Refresh the library panel if present (non-fatal).
        try:
            from PySide6.QtWidgets import QApplication
            from api.manager import APIManager

            # Keep the shared APIManager cache in sync with the on-disk file so
            # any LibraryPanel.refresh() call sees the newly saved part.
            try:
                api = APIManager.get_instance()
                if getattr(api, "library", None) is not None:
                    api.library.reload()
                # Notify subscribers (e.g. LibraryPanel) so the tree refreshes
                # live without needing a restart.  This is the reliable path:
                # QApplication.activeWindow() returns the wizard itself while it
                # is still the modal window, so the direct lookup below misses.
                if hasattr(api, "dispatch"):
                    api.dispatch("library_changed", {"part_id": part_id})
            except Exception:
                pass

            window = QApplication.activeWindow()
            if window and hasattr(window, "library_panel") and hasattr(
                window.library_panel, "refresh"
            ):
                window.library_panel.refresh()
        except Exception:
            pass

        super().accept()

    # -- private -----------------------------------------------------------
    def _prefill_from_device(self, device: Any) -> None:
        """Populate metadata and pin rows from an existing generic device."""
        lib_id = getattr(device, "library_id", None) or getattr(device, "label", None) or ""
        if lib_id:
            self.metadata_page.id_input.setText(str(lib_id).upper().replace(" ", "-"))
        if getattr(device, "label", None):
            self.metadata_page.name_input.setText(str(device.label))
        meta = getattr(device, "meta", None) or {}
        if isinstance(meta, dict):
            if meta.get("manufacturer"):
                self.metadata_page.manufacturer_input.setText(str(meta["manufacturer"]))
            if meta.get("part_number"):
                self.metadata_page.part_number_input.setText(str(meta["part_number"]))
            if meta.get("category"):
                self.metadata_page.category_input.setText(str(meta["category"]))
        self.pinning_page.prefill_from_pins(getattr(device, "pins", []) or [])

    def _prefill_from_library_part(self, part_id: str) -> None:
        """Load an existing saved part and pre-populate every wizard page."""
        part: Optional[Dict[str, Any]] = None
        try:
            from core.library_manager import LibraryManager

            part = LibraryManager().get_part(part_id)
        except Exception:
            part = None
        if not isinstance(part, dict):
            return

        m = self.metadata_page
        # Part ID is the identity key — lock it so an edit can't fork a new part.
        m.id_input.setText(str(part_id))
        m.id_input.setReadOnly(True)
        m.name_input.setText(str(part.get("name") or part_id))
        m.manufacturer_input.setText(str(part.get("manufacturer") or ""))
        m.part_number_input.setText(str(part.get("part_number") or ""))
        m.category_input.setText(str(part.get("category") or ""))
        if part.get("description"):
            m.description_input.setPlainText(str(part["description"]))

        # Preserve the stored SVG (a string, not a file path) unless replaced.
        svg_body = part.get("svg_body")
        if svg_body:
            self._existing_svg_body = svg_body
            m.svg_path_input.setText(
                _i18n("device_wizard_existing_svg", "(existing SVG — browse to replace)")
            )

        if part.get("width_mm") is not None:
            self.scale_page.width_mm.setValue(float(part["width_mm"]))
        if part.get("height_mm") is not None:
            self.scale_page.height_mm.setValue(float(part["height_mm"]))

        self.pinning_page.prefill_from_pin_dicts(part.get("pins", []) or [])

    def _apply_saved_part_to_source_device(self, part_id: str, data: Dict[str, Any]) -> None:
        """Update the promoted source device in place so its canvas item can redraw."""
        device = self.source_device
        if device is None:
            return
        # Delegate the model mutation to the API so the UI layer never mutates
        # the model directly (enforced by test_ui_mvc_static_enforcement).
        try:
            from api.manager import APIManager

            APIManager.get_instance().apply_library_part_to_device(device, part_id, data)
        except Exception:
            pass

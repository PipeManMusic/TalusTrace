"""Smoke tests for the 3-page Device Wizard.

Covers:
  * Construction of all three pages.
  * Library-only save on accept().
  * Promotion flow: pins pre-filled from a source generic device.
  * Metadata-page validation (part_id required, allowed chars only).
  * End-to-end click-through: Next -> Next -> Finish drives the wizard
    without any manual interaction (see ``test_wizard_click_through_*``).
"""
import os
import yaml
import pytest
from unittest.mock import patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWizard, QMessageBox

from core.library_manager import LibraryManager
from core.device import Device
from core.pin import Pin
from ui.items.device import DeviceItem, QSvgRenderer
from ui.main_window import MainWindow
from ui.dialogs.device_wizard import DeviceWizard


@pytest.fixture
def isolated_library(tmp_path):
    """Redirect LibraryManager writes/reads to a tmp parts.yaml."""
    (tmp_path / "parts.yaml").write_text("parts: {}\n")
    patcher = patch.object(
        LibraryManager,
        "_resolve_path",
        lambda self, filename: str(tmp_path / filename),
    )
    patcher.start()
    yield tmp_path
    patcher.stop()


def _read_parts(tmp_path):
    data = yaml.safe_load((tmp_path / "parts.yaml").read_text()) or {}
    return data.get("parts", data) or {}


def test_wizard_has_three_pages(qtbot):
    wizard = DeviceWizard()
    qtbot.addWidget(wizard)
    assert wizard.pageIds() == [0, 1, 2]
    assert wizard.metadata_page is not None
    assert wizard.scale_page is not None
    assert wizard.pinning_page is not None


def test_metadata_page_blocks_until_required_fields_valid(qtbot):
    wizard = DeviceWizard()
    qtbot.addWidget(wizard)
    page = wizard.metadata_page
    assert not page.isComplete()
    page.id_input.setText("BAD ID!")  # space / punctuation not allowed
    page.name_input.setText("X")
    assert not page.isComplete()
    page.id_input.setText("GOOD-ID_01")
    assert page.isComplete()


def test_wizard_saves_part_to_library(qtbot, isolated_library):
    wizard = DeviceWizard()
    qtbot.addWidget(wizard)
    wizard.metadata_page.id_input.setText("DT04-4P")
    wizard.metadata_page.name_input.setText("Deutsch DT04 4-Pin")
    wizard.metadata_page.manufacturer_input.setText("Deutsch")
    wizard.metadata_page.part_number_input.setText("DT04-4P")
    wizard.metadata_page.category_input.setText("Connectors")
    wizard.scale_page.width_mm.setValue(18.5)
    wizard.scale_page.height_mm.setValue(12.0)
    # Page 3 default-populates pins via initializePage; force it
    wizard.pinning_page.initializePage()
    wizard.accept()

    parts = _read_parts(isolated_library)
    assert "DT04-4P" in parts
    entry = parts["DT04-4P"]
    assert entry["manufacturer"] == "Deutsch"
    assert entry["width_mm"] == pytest.approx(18.5)
    assert entry["height_mm"] == pytest.approx(12.0)
    assert isinstance(entry["pins"], list)
    assert len(entry["pins"]) >= 1
    assert "head" in entry["pins"][0] and "tail" in entry["pins"][0]


def test_promotion_prefills_pins_from_source_device(qtbot, isolated_library):
    pins = [
        Pin(x=1.0, y=2.0, label="A", signal="PWR"),
        Pin(x=3.0, y=4.0, label="B", signal="GND"),
    ]
    source = Device(label="Generic Thingy", pins=pins, meta={"manufacturer": "ACME"})
    wizard = DeviceWizard(source_device=source)
    qtbot.addWidget(wizard)

    # Metadata pre-filled
    assert wizard.metadata_page.name_input.text() == "Generic Thingy"
    assert wizard.metadata_page.manufacturer_input.text() == "ACME"
    # Pin table pre-filled with 2 rows from source
    assert wizard.pinning_page.table.rowCount() == 2

    # Override id to satisfy required field, then save
    wizard.metadata_page.id_input.setText("PROMOTED-PART")
    wizard.accept()

    parts = _read_parts(isolated_library)
    assert "PROMOTED-PART" in parts
    entry = parts["PROMOTED-PART"]
    assert entry["promotion_source_id"] == source.id
    assert len(entry["pins"]) == 2
    assert entry["pins"][0]["label"] == "A"
    assert entry["pins"][0]["signal"] == "PWR"


def test_wizard_svg_body_round_trips_into_instantiated_device(qtbot, isolated_library, clean_api_singleton):
    svg_text = """<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'>
  <rect x='0' y='0' width='10' height='10' fill='#123456'/>
</svg>
"""
    svg_path = isolated_library / "body.svg"
    svg_path.write_text(svg_text, encoding="utf-8")

    wizard = DeviceWizard()
    qtbot.addWidget(wizard)
    wizard.metadata_page.id_input.setText("SVG-PART-01")
    wizard.metadata_page.name_input.setText("SVG Part")
    wizard.metadata_page.svg_path_input.setText(str(svg_path))
    wizard.accept()

    api = clean_api_singleton
    api.library = LibraryManager(resource_dir=str(isolated_library))

    device = api.create_device_from_part("SVG-PART-01")

    assert device.svg_body == svg_text
    item = DeviceItem(device)
    if QSvgRenderer is not None:
        assert item._svg_renderer is not None
        assert item._svg_renderer.isValid()


def test_promotion_updates_source_device_svg_on_canvas(qtbot, isolated_library, clean_api_singleton, tmp_path):
    svg_text = "<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><rect x='0' y='0' width='10' height='6' fill='#ff0000'/></svg>"
    svg_path = tmp_path / "promo.svg"
    svg_path.write_text(svg_text, encoding="utf-8")

    api = clean_api_singleton
    source = Device(
        label="Generic Thingy",
        pins=[Pin(x=1.0, y=1.0, label="1", signal="")],
        meta={"manufacturer": "ACME", "width_mm": 10.0, "height_mm": 6.0},
    )
    api.context.harness.devices.append(source)

    window = MainWindow()
    window.api = api
    api.main_window = window
    qtbot.addWidget(window)
    window.show()
    window.canvas.load_harness(api.context.harness)

    wizard = DeviceWizard(source_device=source)
    qtbot.addWidget(wizard)
    wizard.metadata_page.id_input.setText("PROMO-SVG-01")
    wizard.metadata_page.svg_path_input.setText(str(svg_path))
    wizard.accept()

    window.canvas.load_harness(api.context.harness)
    scene_item = next(
        (
            item
            for item in window.canvas.scene.items()
            if hasattr(item, "model") and getattr(item.model, "id", None) == source.id
        ),
        None,
    )

    assert source.library_id == "PROMO-SVG-01"
    assert source.svg_body == svg_text
    assert scene_item is not None
    if QSvgRenderer is not None:
        assert getattr(scene_item, "_svg_renderer", None) is not None
        assert scene_item._svg_renderer.isValid()


# ---------------------------------------------------------------------------
# End-to-end click-through tests
# ---------------------------------------------------------------------------
#
# These tests drive the wizard the way a real user does: by clicking the
# Next / Finish buttons on the underlying QWizard. No manual interaction is
# required — qtbot dispatches the clicks programmatically.
# ---------------------------------------------------------------------------


def _next_button(wizard: DeviceWizard):
    """Return the QWizard Next button (text varies by platform/locale)."""
    return wizard.button(QWizard.NextButton)


def _finish_button(wizard: DeviceWizard):
    """Return the QWizard Finish button."""
    return wizard.button(QWizard.FinishButton)


def _click_through_wizard(qtbot, wizard: DeviceWizard) -> None:
    """Click Next, Next, Finish — exactly as a user would."""
    # Wizard must be shown for buttons to be enabled / sized.
    wizard.show()
    qtbot.waitExposed(wizard)

    # Page 0 -> Page 1
    assert wizard.currentId() == 0
    assert _next_button(wizard).isEnabled(), "Next should be enabled after metadata is valid"
    qtbot.mouseClick(_next_button(wizard), Qt.LeftButton)
    qtbot.waitUntil(lambda: wizard.currentId() == 1, timeout=2000)

    # Page 1 -> Page 2
    qtbot.mouseClick(_next_button(wizard), Qt.LeftButton)
    qtbot.waitUntil(lambda: wizard.currentId() == 2, timeout=2000)

    # Page 2: click Finish
    finish = _finish_button(wizard)
    assert finish.isEnabled(), "Finish should be enabled on the last page"
    qtbot.mouseClick(finish, Qt.LeftButton)
    qtbot.waitUntil(lambda: not wizard.isVisible(), timeout=2000)


def test_wizard_click_through_creates_library_entry(qtbot, isolated_library):
    """Full user-flow: fill page 1, click Next, Next, Finish (no manual clicks)."""
    wizard = DeviceWizard()
    qtbot.addWidget(wizard)

    # Fill required fields on page 1 so Next becomes enabled.
    wizard.metadata_page.id_input.setText("CLICK-THRU-01")
    wizard.metadata_page.name_input.setText("Click-through Test")

    _click_through_wizard(qtbot, wizard)

    assert wizard.last_saved_part_id == "CLICK-THRU-01"
    parts = _read_parts(isolated_library)
    assert "CLICK-THRU-01" in parts


def test_wizard_click_through_aborts_when_required_fields_missing(qtbot):
    """With empty required fields, Next must stay disabled on page 1."""
    wizard = DeviceWizard()
    qtbot.addWidget(wizard)
    wizard.show()
    qtbot.waitExposed(wizard)
    assert wizard.currentId() == 0
    # Required fields empty -> Next disabled -> clicking is a no-op.
    next_btn = _next_button(wizard)
    assert not next_btn.isEnabled()
    qtbot.mouseClick(next_btn, Qt.LeftButton)
    assert wizard.currentId() == 0  # still on metadata page
    wizard.close()


def test_wizard_missing_id_shows_error_instead_of_saving(qtbot, isolated_library, monkeypatch):
    """If ``accept()`` is reached with an empty Part ID, a QMessageBox pops up.

    We auto-dismiss it via monkeypatch so no human click is needed; the test
    verifies nothing was written to the library.
    """
    warnings = []

    def fake_warning(*args, **kwargs):
        warnings.append(args)
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", staticmethod(fake_warning))

    wizard = DeviceWizard()
    qtbot.addWidget(wizard)
    # Bypass QWizard validation: call accept() directly with an empty part_id.
    wizard.accept()

    assert warnings, "Expected a warning dialog when Part ID is missing"
    assert wizard.last_saved_part_id is None
    assert _read_parts(isolated_library) == {}


def _seed_part(tmp_path, part_id="EDIT-ME", **overrides):
    """Write a single part into the isolated library and return its dict."""
    part = {
        "manufacturer": "ACME",
        "part_number": "PN-1",
        "category": "Connectors",
        "description": "Original description",
        "name": "Original Name",
        "width_mm": 20.0,
        "height_mm": 10.0,
        "svg_body": (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 10'>"
            "<rect width='20' height='10' fill='#111'/></svg>"
        ),
        "pins": [
            {"id": "1", "label": "A", "signal": "PWR", "x": 1.0, "y": 2.0,
             "head": [1.0, 2.0], "tail": [1.5, 2.5]},
            {"id": "2", "label": "B", "signal": "GND", "x": 3.0, "y": 4.0,
             "head": [3.0, 4.0], "tail": [3.5, 4.5]},
        ],
    }
    part.update(overrides)
    (tmp_path / "parts.yaml").write_text(yaml.safe_dump({"parts": {part_id: part}}))
    return part


def test_edit_wizard_prefills_all_pages_from_saved_part(qtbot, isolated_library):
    """Launching in edit mode pre-populates metadata, scale, SVG and pins."""
    _seed_part(isolated_library, part_id="EDIT-ME")

    wizard = DeviceWizard(edit_part_id="EDIT-ME")
    qtbot.addWidget(wizard)

    m = wizard.metadata_page
    assert m.id_input.text() == "EDIT-ME"
    assert m.id_input.isReadOnly(), "Part ID must be locked while editing"
    assert m.name_input.text() == "Original Name"
    assert m.manufacturer_input.text() == "ACME"
    assert m.category_input.text() == "Connectors"
    assert wizard.scale_page.width_mm.value() == pytest.approx(20.0)
    assert wizard.scale_page.height_mm.value() == pytest.approx(10.0)
    assert wizard.pinning_page.table.rowCount() == 2
    # Existing SVG is preserved even though no file path was chosen.
    assert wizard._existing_svg_body is not None


def test_edit_wizard_saves_changes_without_losing_svg(qtbot, isolated_library):
    """Editing width and saving keeps the original SVG and updates the value."""
    original = _seed_part(isolated_library, part_id="EDIT-ME")

    wizard = DeviceWizard(edit_part_id="EDIT-ME")
    qtbot.addWidget(wizard)
    wizard.scale_page.width_mm.setValue(33.0)
    wizard.accept()

    parts = _read_parts(isolated_library)
    assert "EDIT-ME" in parts
    entry = parts["EDIT-ME"]
    assert entry["width_mm"] == pytest.approx(33.0)
    # SVG body must survive the edit (no new file was chosen).
    assert entry["svg_body"] == original["svg_body"]
    # No duplicate part was created under a different id.
    assert list(parts.keys()) == ["EDIT-ME"]

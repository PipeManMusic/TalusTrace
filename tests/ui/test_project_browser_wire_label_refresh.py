"""
Regression test: the project browser's wire label must refresh when the source
or destination device/pin is renamed.

A wire's displayed name is derived from its endpoint device/pin labels. Renaming
a device dispatches ``model_changed`` with ``action='update'``; the browser must
rebuild so the derived wire label reflects the new name.
"""
import uuid

import pytest

from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.wire import Wire
from ui.panels.project_browser import ProjectBrowser, ROLE_KIND, ROLE_ID


def _new_id():
    return str(uuid.uuid4())


@pytest.fixture
def api():
    APIManager.reset()
    return APIManager.get_instance()


def _wire_labels(browser):
    """Return the display text of every wire node in the tree."""
    labels = []
    root = browser.tree.invisibleRootItem()
    for i in range(root.childCount()):
        cat = root.child(i)
        if cat.data(0, ROLE_KIND) == "category" and cat.data(0, ROLE_ID) == "wire":
            for j in range(cat.childCount()):
                labels.append(cat.child(j).text(0))
    return labels


def test_wire_label_refreshes_on_device_rename(qtbot, api):
    src_pin, dst_pin = _new_id(), _new_id()
    src = Device(id=_new_id(), label="SRC", pins=[Pin(id=src_pin, label="A")])
    dst = Device(id=_new_id(), label="DST", pins=[Pin(id=dst_pin, label="B")])
    wire = Wire(id=_new_id(), from_conn=src.id, from_pin=src_pin,
                to_conn=dst.id, to_pin=dst_pin)
    api.context.harness.devices.append(src)
    api.context.harness.devices.append(dst)
    api.context.harness.wires.append(wire)

    browser = ProjectBrowser()
    qtbot.addWidget(browser)

    assert any("SRC" in lbl for lbl in _wire_labels(browser))

    # Rename the source device and emit the same event the edit command sends.
    src.label = "RENAMED"
    api.dispatch("model_changed", {"action": "update", "item": src})
    qtbot.wait(50)  # allow the coalesced deferred refresh to run

    labels = _wire_labels(browser)
    assert any("RENAMED" in lbl for lbl in labels), labels
    assert not any("SRC" in lbl for lbl in labels), labels

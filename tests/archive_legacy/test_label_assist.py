from PySide6.QtWidgets import QApplication

from talustrace.frontend.items import DeviceItem
from talustrace.backend.models import Device
from talustrace.backend.labels import LabelManager


def test_label_suggestion():
    app = QApplication.instance() or QApplication([])
    dev = Device(id="D1", label="Coolant Temp", pins=0)
    item = DeviceItem(dev)
    code = item.suggest_code()
    assert code == "CLNT_TMP"


def test_set_label_updates_model_and_text():
    app = QApplication.instance() or QApplication([])
    dev = Device(id="D1", label="Old", pins=0)
    changed = {"dirty": False}

    def mark():
        changed["dirty"] = True

    item = DeviceItem(dev, on_changed=mark)
    item.set_label("NEWLBL")

    assert dev.label == "NEWLBL"
    assert item.label.text() == "NEWLBL"
    assert changed["dirty"] is True

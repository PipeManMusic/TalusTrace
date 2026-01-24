import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot
from ui.canvas import HarnessCanvas
from core.device import Device
from api.manager import APIManager

@pytest.fixture
def canvas_and_api(qtbot: QtBot):
    APIManager.reset()
    api = APIManager.get_instance()
    canvas = HarnessCanvas()
    qtbot.addWidget(canvas)
    canvas.show()
    api.main_window = type("FakeMainWindow", (), {"canvas": canvas})()
    return canvas, api, qtbot

def test_device_add_remove_contract(canvas_and_api):
    canvas, api, qtbot = canvas_and_api
    import uuid
    device = Device(id=str(uuid.uuid4()), x=10, y=10)
    # Add device via API
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
        api.dispatch("model_changed", {"action": "add", "item": device})
        qtbot.wait(100)  # Let event loop process
        # Assert device is in scene
        items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
        assert items, "DeviceItem not added to scene."
        # Remove device via API
        api.context.harness.devices.remove(device)
        api.dispatch("model_changed", {"action": "remove", "item": device})
        qtbot.wait(100)
        # Assert device is removed from scene
        items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
        assert not items, "DeviceItem still present in scene after removal."

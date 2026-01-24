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

def test_device_delete_via_delete_key(canvas_and_api):
    canvas, api, qtbot = canvas_and_api
    import uuid
    device = Device(id=str(uuid.uuid4()), x=10, y=10)
    # Add device via API
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
        api.dispatch("model_changed", {"action": "add", "item": device})
        qtbot.wait(100)
        # Find DeviceItem in scene
        items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
        assert items, "DeviceItem not added to scene."
        device_item = items[0]
        # Select the device visually
        if hasattr(device_item, 'setSelected'):
            device_item.setSelected(True)
        qtbot.wait(50)
        # Simulate Delete key event to the canvas
        qtbot.keyClick(canvas, Qt.Key_Delete)
        qtbot.wait(200)
        # Assert DeviceItem is removed from scene
        items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
        assert not items, "DeviceItem still present in scene after deletion."

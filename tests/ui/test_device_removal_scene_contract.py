import pytest
from PySide6.QtWidgets import QApplication
from ui.canvas import HarnessCanvas
from core.device import Device
from api.manager import APIManager
import sys

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def canvas_and_api(qapp):
    APIManager.reset()
    api = APIManager.get_instance()
    canvas = HarnessCanvas()
    canvas.show()  # Needed for scene updates
    api.main_window = type("FakeMainWindow", (), {"canvas": canvas})()
    return canvas, api

def test_device_removal_removes_scene_item(canvas_and_api):
    canvas, api = canvas_and_api
    import uuid
    device = Device(id=str(uuid.uuid4()), x=10, y=10)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
        api.dispatch("model_changed", {"action": "add", "item": device})
        # DeviceItem should be in the scene
        items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
        assert items, "DeviceItem not added to scene."
        # Remove device
        api.context.harness.devices.remove(device)
        api.dispatch("model_changed", {"action": "remove", "item": device})
        # DeviceItem should be gone
        items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) == device.id]
        assert not items, "DeviceItem still present in scene after removal."

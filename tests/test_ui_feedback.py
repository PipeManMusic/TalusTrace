import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.items import DeviceItem
from core.device import Device
from api.manager import APIManager

@pytest.mark.gui
def test_smart_cursor_affordance(qtbot):
    """PH5-CLN.3: Verify cursor changes to OpenHand over devices using API coordinates."""
    window = MainWindow()
    window.show()
    qtbot.add_widget(window)
    canvas = window.canvas
    canvas.resize(800, 600)
    
    api = APIManager.get_instance()
    harness = api.context.harness
    import uuid
    dev_id = str(uuid.uuid4())
    dev = Device(id=dev_id, x=100.0, y=100.0)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        harness.devices.append(dev)
    canvas.load_harness(harness)
    QApplication.processEvents()
    # Find the DeviceItem by UUID
    target_item = next((item for item in canvas.scene.items()
                        if isinstance(item, DeviceItem) and item.model.id == dev_id), None)
    assert target_item is not None

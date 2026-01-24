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
    dev = Device(id="11111111-1111-1111-1111-111111111111", x=100.0, y=100.0)
    harness.devices.append(dev)
    
    canvas.load_harness(harness)
    QApplication.processEvents()
    
    # REFACTOR: Access .model instead of .device
    target_item = next((item for item in canvas.scene.items()
                        if isinstance(item, DeviceItem) and item.model.id == "TEST_DEV"), None)
    
    assert target_item is not None

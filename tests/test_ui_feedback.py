from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device
from ui.items import DeviceItem
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF


def test_smart_cursor_affordance(qtbot):
    """PH5-CLN.3: Verify cursor changes to OpenHand over devices using API coordinates."""
    window = MainWindow()
    window.show()
    qtbot.add_widget(window)
    canvas = window.canvas
    canvas.resize(800, 600)
    
    # 1. Inject Device via API
    api = APIManager.get_instance()
    harness = api.context.harness
    target_x, target_y = 100.0, 100.0
    dev = Device(id="TEST_DEV", x=target_x, y=target_y)
    harness.devices.append(dev)
    
    canvas.load_harness(harness)
    
    # 2. Sync and Verify
    QApplication.processEvents()
    qtbot.wait(100)
    
    target_item = next((item for item in canvas.scene.items() 
                       if isinstance(item, DeviceItem) and item.device.id == "TEST_DEV"), None)
    assert target_item is not None

    # 3. Robustly scan inside the bounding rect for OpenHandCursor
    rect = target_item.sceneBoundingRect()
    found = False
    for dx in range(int(rect.width())):
        for dy in range(int(rect.height())):
            pt = rect.topLeft() + QPointF(dx + 1, dy + 1)
            target_pixel = canvas.mapFromScene(pt)
            qtbot.mouseMove(canvas.viewport(), target_pixel)
            QApplication.processEvents()
            qtbot.wait(5)
            if canvas.viewport().cursor().shape() == Qt.OpenHandCursor:
                found = True
                break
        if found:
            break
    assert found, "OpenHandCursor should be set when hovering over DeviceItem's bounding rect"
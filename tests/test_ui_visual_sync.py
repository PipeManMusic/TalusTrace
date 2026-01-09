import pytest
from PySide6.QtWidgets import QApplication
from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.wire import Wire
from core.enums import Side
from ui.main_window import MainWindow
from ui.items import BundleItem, DeviceItem



def test_wire_follows_device_drag(qtbot):
    window = MainWindow()
    qtbot.add_widget(window)
    api = APIManager.get_instance()
    
    # Setup data with matching Pin IDs
    d1 = Device(id="D1", x=0, y=0)
    d1.pins.append(Pin(id="P1", x=0, y=0, side=Side.LEFT))
    # Ensure wire endpoints match pin ids exactly
    d2 = Device(id="D2", x=100, y=100)
    d2.pins.append(Pin(id="P1", x=0, y=0, side=Side.RIGHT))
    
    w1 = Wire(id="W1", from_conn="D1", from_pin="P1", to_conn="D2", to_pin="P1")
    
    api.context.harness.devices = [d1, d2]
    api.context.harness.wires = [w1]
    
    # Load and force a processEvents to allow Qt to instantiate items
    window.canvas.load_harness(api.context.harness)
    QApplication.processEvents()
    
    items = window.canvas.scene.items()
    wire_item = next((i for i in items if isinstance(i, BundleItem)), None)
    device_item = next((i for i in items if isinstance(i, DeviceItem) and i.device == d1), None)
    
    assert wire_item is not None, "BundleItem not found - check Wire/Pin ID matching"
    
    from tools.move_tool import MoveTool
    tool = MoveTool()
    tool.start(d1, device_item)
    tool.update(50, 50) 
    
    # Path node 0 should match the new world position of D1.P1 (0+50, 0+50)
    assert wire_item.path_nodes[0] == (50.0, 50.0)
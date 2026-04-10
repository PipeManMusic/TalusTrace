import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.wire import Wire
from core.harness import DeviceList
from infra.context import Context
import uuid
from PySide6.QtCore import Qt, QPointF


def test_wire_context_menu_delete_removes_wire(qtbot):
    """
    Contract: Triggering 'Delete' from the wire context menu must remove the wire
    from the model AND the canvas scene.
    """
    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    api = APIManager(context=Context())
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)

    # Add two devices with pins
    dev1_id = str(uuid.uuid4())
    pin1_id = str(uuid.uuid4())
    dev2_id = str(uuid.uuid4())
    pin2_id = str(uuid.uuid4())

    dev1 = Device(id=dev1_id, x=100, y=100, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin1 = Pin(id=pin1_id, x=10, y=10, device_id=dev1_id)
    dev1.pins.append(pin1)

    dev2 = Device(id=dev2_id, x=300, y=100, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin2 = Pin(id=pin2_id, x=10, y=10, device_id=dev2_id)
    dev2.pins.append(pin2)

    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev1)
        api.context.harness.devices.append(dev2)

    # Create a wire between pin1 and pin2
    wire_id = str(uuid.uuid4())
    wire = Wire(
        id=wire_id,
        from_conn=dev1_id, from_pin=pin1_id,
        to_conn=dev2_id, to_pin=pin2_id,
        path_nodes=[[100, 100], [300, 100]],
    )
    api.context.harness.wires.append(wire)

    # Load harness (creates scene items)
    window.canvas.load_harness(api.context.harness)

    # Verify wire is in scene
    wire_item = api.get_scene_item(wire_id)
    assert wire_item is not None, "WireItem not found in scene registry after load."
    assert wire in api.context.harness.wires, "Wire not in harness."

    # Now simulate the context menu delete flow exactly as it happens in the live app:
    # 1. context_menu_manager._execute sets api.context.wire
    # 2. registry.execute("edit.delete", api.context) calls edit_delete
    # 3. edit_delete calls api.delete_wire(context.wire)
    # 4. DeleteWireCommand dispatches model_changed("remove")
    # 5. canvas on_model_changed removes scene item
    from ui.context_menu_manager import ContextMenuManager
    from api.actions import actions_map
    mgr = ContextMenuManager(config=api._config if hasattr(api, '_config') else {}, actions_map_override=actions_map)
    mgr._context_item = wire_item
    delete_uuid = "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b"
    mgr._execute(delete_uuid)

    # Verify wire removed from model
    assert wire not in api.context.harness.wires, "Wire still in harness after delete."
    # Verify wire removed from scene registry
    assert api.get_scene_item(wire_id) is None, "WireItem still in scene registry after delete."
    # Verify wire item removed from scene
    scene_items = window.canvas.scene.items()
    assert wire_item not in scene_items, "WireItem still in QGraphicsScene after delete."

    window.close()

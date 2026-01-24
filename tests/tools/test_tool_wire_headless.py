import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt

def test_wire_creation_flow(fresh_api, create_test_wire):
    from tools.wire_tool import WireTool
    from core.pin import Pin
    from core.device import Device
    from ui.items.pin import PinItem

    # 1. Setup Data
    import uuid
    dev1 = Device(id=str(uuid.uuid4()), x=0, y=0)
    import uuid
    pin1 = Pin(id=str(uuid.uuid4()), x=10, y=10)
    dev1.pins.append(pin1)
    
    dev2 = Device(id=str(uuid.uuid4()), x=100, y=0)
    pin2 = Pin(id=str(uuid.uuid4()), x=110, y=10)
    dev2.pins.append(pin2)

    # 2. Setup Mock Items
    mock_pin_item_1 = MagicMock(spec=PinItem)
    mock_pin_item_1.pin = pin1
    mock_dev_item_1 = MagicMock()
    mock_dev_item_1.model = dev1
    mock_pin_item_1.parentItem.return_value = mock_dev_item_1
    mock_pin_item_1.mapToScene.return_value = QPointF(10, 10)
    mock_pin_item_1.pos.return_value = QPointF(10, 10)

    mock_pin_item_2 = MagicMock(spec=PinItem)
    mock_pin_item_2.pin = pin2
    mock_dev_item_2 = MagicMock()
    mock_dev_item_2.model = dev2
    mock_pin_item_2.parentItem.return_value = mock_dev_item_2
    mock_pin_item_2.mapToScene.return_value = QPointF(110, 10)
    mock_pin_item_2.pos.return_value = QPointF(110, 10)

    # 3. Configure Scene Mock (items method)
    def items_side_effect(*args, **kwargs):
        # If no args, return all items (used by _get_pin_scene_pos)
        if not args:
            return [mock_pin_item_1, mock_pin_item_2]
        pos = args[0]
        x = pos.x()
        if abs(x - 10) < 5:
            return [mock_pin_item_1]
        if abs(x - 110) < 5:
            return [mock_pin_item_2]
        return []
    fresh_api.scene.items.side_effect = items_side_effect

    # 4. Initialize Tool & Mock Tool Manager
    tool = WireTool()
    tool._api_instance = fresh_api
    # MOCK THIS: Prevent actual tool switching
    from unittest.mock import MagicMock as MM
    fresh_api.tool_manager = MM()

    # 5. Act: Click Pin 1
    event_p1 = MagicMock()
    event_p1.scene_pos = QPointF(10, 10)
    event_p1.original_event.button.return_value = Qt.LeftButton

    tool.on_mouse_press(event_p1)

    import uuid
    assert tool.state == "DRAGGING", "Tool should enter DRAGGING state after clicking a pin"
    # Check that start_pin.id is a valid UUID
    try:
        uuid_obj = uuid.UUID(tool.start_pin.id)
    except Exception:
        assert False, f"Pin id is not a valid UUID: {tool.start_pin.id}"

    # 6. Act: Click Pin 2
    event_p2 = MagicMock()
    event_p2.scene_pos = QPointF(110, 10)
    event_p2.original_event.button.return_value = Qt.LeftButton

    # Mock Undo Stack
    fresh_api.context.undo_stack = MM()

    tool.on_mouse_press(event_p2)

    assert tool.state == "IDLE", "Tool should reset to IDLE after creating wire"
    assert fresh_api.context.undo_stack.push.called, "Undo command should be pushed"
    # Assert tool switch happened
    fresh_api.tool_manager.set_tool.assert_called_with('select')
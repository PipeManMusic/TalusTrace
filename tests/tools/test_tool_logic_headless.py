import pytest
from PySide6.QtCore import Qt, QPointF
from unittest.mock import MagicMock
from ui.items import WireItem  # Added import
from tools.select_tool import SelectTool  # Added import

class MockEvent:
    def __init__(self, x, y, button, type='press'):
        self.scene_pos = QPointF(x, y)
        self.button = button
        self.type = type

def test_select_tool_removes_elbow_logic(fresh_api, create_test_wire):
    # 1. Setup Data
    wire = create_test_wire(nodes=[[0,0], [50,50], [100,0]])
    
    # 2. Setup Tool
    tool = SelectTool()
    tool.api = fresh_api 
    
    # 3. Mock Hit Test
    mock_item = MagicMock()
    mock_item.model = wire
    fresh_api.scene.itemAt.return_value = mock_item
    
    # 4. Act (Right Click at Elbow)
    event = MockEvent(50, 50, Qt.RightButton)
    tool.on_mouse_press(event)
    
    # 5. Assert (Model Changed)
    assert len(wire.path_nodes) == 2

class DummyEvent:
    def __init__(self, scene_pos, button=1, event_type=None, scene_item=None):
        self.scene_pos = scene_pos
        self.button = button
        self.type = event_type
        self.scene_item = scene_item

class DummyPos:
    def __init__(self, x, y):
        self._x = float(x)
        self._y = float(y)
    def x(self): return self._x
    def y(self): return self._y

@pytest.mark.usefixtures("fresh_api")
def test_select_tool_delete_elbow(fresh_api, create_test_wire):
    import uuid
    wire = create_test_wire(id=str(uuid.uuid4()), from_conn="A", to_conn="B", path_nodes=[(0,0), (10,10), (20,20)])
    wire_item = WireItem(wire)
    tool = SelectTool()
    tool.api = fresh_api
    # Simulate right-click at elbow (10,10)
    from PySide6.QtCore import Qt
    event = DummyEvent(DummyPos(10,10), button=Qt.RightButton, scene_item=wire_item)
    fresh_api.remove_elbow = lambda model, idx: model.path_nodes.pop(idx)
    tool.on_mouse_press(event)
    assert len(wire.path_nodes) == 2
    assert (10.0,10.0) not in wire.path_nodes

@pytest.mark.usefixtures("fresh_api")
def test_select_tool_add_elbow(fresh_api, create_test_wire):
    import uuid
    wire = create_test_wire(id=str(uuid.uuid4()), from_conn="A", to_conn="B", path_nodes=[(0,0), (20,0)])
    wire_item = WireItem(wire)
    tool = SelectTool()
    tool.api = fresh_api
    # Simulate double-click on segment
    event = DummyEvent(DummyPos(10,0), button=1, event_type='double_click', scene_item=wire_item)
    fresh_api.add_elbow = lambda model, idx, pos: model.path_nodes.insert(idx+1, tuple(pos))
    tool.on_mouse_press(event)
    assert len(wire.path_nodes) == 3
    assert (10,0) in wire.path_nodes

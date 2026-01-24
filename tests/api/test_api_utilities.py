
import pytest
import uuid
from api.manager import APIManager
from infra.context import Context
from core.device import Device
from core.wire import Wire

# Test: add_elbow, remove_elbow, move_segment utility methods

def test_api_add_and_remove_elbow():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    import uuid
    wire = Wire(id=str(uuid.uuid4()), path_nodes=[[0, 0], [10, 0]])
    ctx.harness.wires.append(wire)
    # Add elbow
    api.add_elbow(wire, 1, [5, 5])
    assert [5, 5] in wire.path_nodes
    # Remove elbow
    api.remove_elbow(wire, 1)
    assert [5, 5] not in wire.path_nodes


def test_api_move_segment():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    wire = Wire(id=str(uuid.uuid4()), path_nodes=[[0, 0], [10, 0], [20, 0]])
    ctx.harness.wires.append(wire)
    # Move segment (move [10,0] to [10,10])
    # Move segment (move [10,0] to [10,10])
    # The MoveSegmentCommand expects delta values, not positions
    api.move_segment(wire, 0, 1, 0, 10)
    assert wire.path_nodes[1] == [10, 10]


def test_api_deselect_all():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    # Simulate selection (if selection manager is present)
    if hasattr(api, 'selection_manager'):
        api.selection_manager.selected_models = [Device(id="d1", x=0, y=0)]
        api.deselect_all()
        assert not api.selection_manager.selected_models
    else:
        # No-op if selection manager is not present
        api.deselect_all()

# Test: undo/redo with empty stack
def test_api_undo_redo_empty_stack():
    ctx = Context()
    api = APIManager.get_instance(context=ctx)
    # Should not raise
    ctx.undo_stack.undo()
    ctx.undo_stack.redo()

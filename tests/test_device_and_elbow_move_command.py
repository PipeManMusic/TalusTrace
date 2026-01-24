import pytest
from unittest.mock import MagicMock

# Dummy device model for TDD
class DummyDevice:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

# Dummy wire model for TDD
class DummyWire:
    def __init__(self, path_nodes):
        self.path_nodes = [list(node) for node in path_nodes]

# DeviceMoveCommand for TDD
class DeviceMoveCommand:
    def __init__(self, device, old_pos, new_pos, dispatcher=None):
        self.device = device
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.dispatcher = dispatcher
    def execute(self):
        self.device.x, self.device.y = self.new_pos
        if self.dispatcher:
            self.dispatcher('model_changed', {'item': self.device, 'pos': self.new_pos})
    def undo(self):
        self.device.x, self.device.y = self.old_pos
        if self.dispatcher:
            self.dispatcher('model_changed', {'item': self.device, 'pos': self.old_pos})
    def redo(self):
        self.execute()

# ElbowMoveCommand for TDD
class ElbowMoveCommand:
    def __init__(self, wire, index, old_pos, new_pos, dispatcher=None):
        self.wire = wire
        self.index = index
        self.old_pos = list(old_pos)
        self.new_pos = list(new_pos)
        self.dispatcher = dispatcher
    def execute(self):
        self.wire.path_nodes[self.index] = list(self.new_pos)
        if self.dispatcher:
            self.dispatcher('model_changed', {'item': self.wire, 'index': self.index, 'pos': self.new_pos})
    def undo(self):
        self.wire.path_nodes[self.index] = list(self.old_pos)
        if self.dispatcher:
            self.dispatcher('model_changed', {'item': self.wire, 'index': self.index, 'pos': self.old_pos})
    def redo(self):
        self.execute()

def test_device_move_command_executes_and_undos():
    device = DummyDevice(1, 2)
    dispatcher = MagicMock()
    cmd = DeviceMoveCommand(device, (1, 2), (5, 6), dispatcher=dispatcher)
    cmd.execute()
    assert (device.x, device.y) == (5, 6)
    dispatcher.assert_called_with('model_changed', {'item': device, 'pos': (5, 6)})
    cmd.undo()
    assert (device.x, device.y) == (1, 2)
    dispatcher.assert_called_with('model_changed', {'item': device, 'pos': (1, 2)})
    cmd.redo()
    assert (device.x, device.y) == (5, 6)

def test_elbow_move_command_executes_and_undos():
    wire = DummyWire([[0, 0], [10, 10], [20, 20]])
    dispatcher = MagicMock()
    cmd = ElbowMoveCommand(wire, 1, [10, 10], [15, 25], dispatcher=dispatcher)
    cmd.execute()
    assert wire.path_nodes[1] == [15, 25]
    dispatcher.assert_called_with('model_changed', {'item': wire, 'index': 1, 'pos': [15, 25]})
    cmd.undo()
    assert wire.path_nodes[1] == [10, 10]
    dispatcher.assert_called_with('model_changed', {'item': wire, 'index': 1, 'pos': [10, 10]})
    cmd.redo()
    assert wire.path_nodes[1] == [15, 25]

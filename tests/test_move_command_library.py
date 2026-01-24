import pytest
from unittest.mock import MagicMock, patch

# Dummy base move command for TDD
class BaseMoveCommand:
    def __init__(self, target, old_pos, new_pos, dispatcher=None):
        self.target = target
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.dispatcher = dispatcher
        self._executed = False

    def execute(self):
        self._set_pos(self.new_pos)
        self._executed = True
        if self.dispatcher:
            self.dispatcher('model_changed', {'item': self.target, 'pos': self.new_pos})

    def undo(self):
        self._set_pos(self.old_pos)
        if self.dispatcher:
            self.dispatcher('model_changed', {'item': self.target, 'pos': self.old_pos})

    def redo(self):
        self.execute()

    def _set_pos(self, pos):
        self.target.x, self.target.y = pos

# Dummy model
class DummyModel:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

# Dummy subclass for device
class DeviceMoveCommand(BaseMoveCommand):
    pass

def test_base_move_command_executes_and_undos():
    model = DummyModel(1, 2)
    dispatcher = MagicMock()
    cmd = BaseMoveCommand(model, (1, 2), (5, 6), dispatcher=dispatcher)
    cmd.execute()
    assert (model.x, model.y) == (5, 6)
    dispatcher.assert_called_with('model_changed', {'item': model, 'pos': (5, 6)})
    cmd.undo()
    assert (model.x, model.y) == (1, 2)
    dispatcher.assert_called_with('model_changed', {'item': model, 'pos': (1, 2)})
    cmd.redo()
    assert (model.x, model.y) == (5, 6)


def test_device_move_command_inherits_and_works():
    model = DummyModel(10, 20)
    dispatcher = MagicMock()
    cmd = DeviceMoveCommand(model, (10, 20), (30, 40), dispatcher=dispatcher)
    cmd.execute()
    assert (model.x, model.y) == (30, 40)
    cmd.undo()
    assert (model.x, model.y) == (10, 20)


def test_move_command_extensibility():
    class CustomItem:
        def __init__(self):
            self.x = 0
            self.y = 0
            self.extra = 99
    class CustomMoveCommand(BaseMoveCommand):
        def _set_pos(self, pos):
            super()._set_pos(pos)
            self.target.extra = 42  # Custom logic
    item = CustomItem()
    cmd = CustomMoveCommand(item, (0, 0), (7, 8))
    cmd.execute()
    assert (item.x, item.y) == (7, 8)
    assert item.extra == 42
    cmd.undo()
    assert (item.x, item.y) == (0, 0)
    assert item.extra == 42

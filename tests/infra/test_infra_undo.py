import pytest
from unittest.mock import MagicMock
from infra.undo_stack import UndoStack, BaseCommand

class MockCommand(BaseCommand):
    def __init__(self, target_list, value):
        super().__init__("mock")
        self.target_list = target_list
        self.value = value

    def _do_execute(self):
        self.target_list.append(self.value)

    def undo(self):
        self.target_list.remove(self.value)

def test_undo_stack_push_execute():
    """PH5-CMD.1: Stack should execute command immediately on push."""
    stack = UndoStack()
    data = []
    cmd = MockCommand(data, "A")
    
    stack.push(cmd)
    assert "A" in data
    assert stack.can_undo() is True
    assert stack.can_redo() is False

def test_undo_redo_logic():
    """PH5-CMD.1: Validate Undo/Redo pointer movement."""
    stack = UndoStack()
    data = []
    
    # Push A, B
    stack.push(MockCommand(data, "A"))
    stack.push(MockCommand(data, "B"))
    assert data == ["A", "B"]
    
    # Undo B
    stack.undo()
    assert data == ["A"]
    assert stack.can_redo() is True
    
    # Redo B
    stack.redo()
    assert data == ["A", "B"]
    
    # Undo B, Undo A
    stack.undo()
    stack.undo()
    assert data == []
    assert stack.can_undo() is False

def test_stack_truncate_on_branch():
    """PH5-CMD.1: Pushing new command after undo should clear future."""
    stack = UndoStack()
    data = []
    
    stack.push(MockCommand(data, "A"))
    stack.push(MockCommand(data, "B"))
    stack.undo() # State is ["A"], Redo stack has [B]
    
    # Branching: Push C
    stack.push(MockCommand(data, "C"))
    assert data == ["A", "C"]
    assert stack.can_redo() is False # B is lost
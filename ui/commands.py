"""
PH5-CMD.1: Command Pattern Base Classes for UI
Implements the core Command pattern for undo/redo in the Talus Trace UI layer.
"""

class Command:
    """Base class for all commands (PH5-CMD.1)."""
    def __init__(self, description=None):
        self.description = description or self.__class__.__name__
        self._executed = False

    def execute(self):
        """Perform the command action."""
        raise NotImplementedError

    def undo(self):
        """Undo the command action."""
        raise NotImplementedError

    def redo(self):
        """Redo the command action (default: calls execute)."""
        self.execute()

    @property
    def executed(self):
        return self._executed

    def mark_executed(self):
        self._executed = True


class CommandStack:
    """Manages undo/redo stacks for UI commands (PH5-CMD.1)."""
    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []

    def do(self, command: Command):
        command.execute()
        command.mark_executed()
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self):
        if not self._undo_stack:
            return
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self):
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self):
        return bool(self._undo_stack)

    @property
    def can_redo(self):
        return bool(self._redo_stack)

    @property
    def undo_stack(self):
        return list(self._undo_stack)

    @property
    def redo_stack(self):
        return list(self._redo_stack)

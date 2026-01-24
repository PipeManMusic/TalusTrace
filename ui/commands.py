"""
PH5-CMD.1: Command Pattern Base Classes for UI
Implements the core Command pattern for undo/redo in the Talus Trace UI layer.
"""

class Command:
    """Base class for all commands (PH5-CMD.1)."""
    def __init__(self, description=None):
        """Initialize the command with an optional description."""
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
        """Return whether the command has been executed."""
        return self._executed

    def mark_executed(self):
        """Mark the command as executed."""
        self._executed = True


class CommandStack:
    """Manages undo/redo stacks for UI commands (PH5-CMD.1)."""
    def __init__(self):
        """Initialize the command stack with empty undo and redo stacks."""
        self._undo_stack = []
        self._redo_stack = []

    def do(self, command: Command):
        """Execute a command, mark it as executed, and add it to the undo stack."""
        command.execute()
        command.mark_executed()
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self):
        """Undo the last command on the undo stack and move it to the redo stack."""
        if not self._undo_stack:
            return
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self):
        """Redo the last command on the redo stack and move it to the undo stack."""
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)

    def clear(self):
        """Clear both the undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self):
        """Return True if there are commands to undo."""
        return bool(self._undo_stack)

    @property
    def can_redo(self):
        """Return True if there are commands to redo."""
        return bool(self._redo_stack)

    @property
    def undo_stack(self):
        """Return a copy of the undo stack."""
        return list(self._undo_stack)

    @property
    def redo_stack(self):
        """Return a copy of the redo stack."""
        return list(self._redo_stack)

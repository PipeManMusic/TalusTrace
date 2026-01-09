"""
Undo/Redo Stack and Command Pattern for Talus Trace (PH5-CMD.1)
"""

class BaseCommand:
    """Base class for all undoable commands."""
    def __init__(self, description=None):
        self.description = description or self.__class__.__name__
        self._executed = False

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def redo(self):
        self.execute()

    @property
    def executed(self):
        return self._executed

    def mark_executed(self):
        self._executed = True

class UndoStack:
    """Manages undo/redo for commands."""
    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []
        self._callbacks = []

    def subscribe(self, callback):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _notify(self, event_type):
        for cb in self._callbacks:
            try:
                cb(event_type)
            except Exception as e:
                print(f"UndoStack callback error: {e}")

    def push(self, command: BaseCommand):
        self.do(command)

    def do(self, command: BaseCommand):
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
        self._notify('undo')

    def redo(self):
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)
        self._notify('redo')

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    def can_undo(self):
        return bool(self._undo_stack)

    def can_redo(self):
        return bool(self._redo_stack)

    @property
    def undo_stack(self):
        return list(self._undo_stack)

    @property
    def redo_stack(self):
        return list(self._redo_stack)

    def __len__(self):
        return len(self._undo_stack)

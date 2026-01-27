"""
Undo/Redo Stack and Command Pattern for Talus Trace (PH5-CMD.1)
"""


class BaseCommand:
    """Base class for all undoable commands. Enforces dispatcher-only execution."""
    _allow_execute = False  # Class-level flag for dispatcher enforcement

    def __init__(self, description=None):
        """Initialize the base command with an optional description."""
        self.description = description or self.__class__.__name__
        self._executed = False

    def execute(self):
        """Execute the command, enforcing dispatcher-only execution."""
        # Enforce that execute() is only called via dispatcher
        if not getattr(self, '_allow_execute', False):
            raise RuntimeError(f"{self.__class__.__name__}.execute() must be called via dispatcher, not directly!")
        try:
            return self._do_execute()
        finally:
            self._allow_execute = False  # Always reset after execution

    def _do_execute(self):
        """Override this in subclasses with actual command logic."""
        raise NotImplementedError

    def undo(self):
        """Undo the command. Must be implemented by subclasses."""
        raise NotImplementedError

    def redo(self):
        """Redo the command by calling execute()."""
        self.execute()

    @property
    def executed(self):
        """Return True if the command has been executed."""
        return self._executed

    def mark_executed(self):
        """Mark the command as executed."""
        self._executed = True

    @staticmethod
    def dispatch(command, *args, **kwargs):
        """Dispatcher entry point: sets flag and calls execute."""
        command._allow_execute = True
        return command.execute(*args, **kwargs)

class UndoStack:
    """
    Manages undo/redo for commands in the application.
    Provides stack operations, transaction grouping, and callback subscription.
    """
    def begin_transaction(self, description=None):
        """
        Begin a transaction to group multiple commands as one undoable action.
        Args:
            description (str): Optional description for the transaction.
        """
        if hasattr(self, '_transaction_commands') and self._transaction_commands is not None:
            raise RuntimeError("Transaction already in progress")
        self._transaction_commands = []
        self._transaction_description = description or "Transaction"

    def end_transaction(self):
        """
        End the current transaction and push the grouped commands as a single command.
        """
        if not hasattr(self, '_transaction_commands') or self._transaction_commands is None:
            raise RuntimeError("No transaction in progress")
        if not self._transaction_commands:
            self._transaction_commands = None
            return
        group = TransactionCommand(self._transaction_commands, self._transaction_description)
        self.do(group)
        self._transaction_commands = None
        self._transaction_description = None

    def in_transaction(self):
        """
        Return True if a transaction is currently in progress.
        """
        return hasattr(self, '_transaction_commands') and self._transaction_commands is not None

    def is_empty(self):
        """
        Return True if the undo stack is empty.
        """
        return not self._undo_stack

    def __init__(self):
        """
        Initialize the UndoStack with empty undo/redo stacks and callbacks.
        """
        """
        Initialize the UndoStack with empty undo/redo stacks and no active transaction.
        """
        self._undo_stack = []
        self._redo_stack = []
        self._current_transaction = None
        self._transaction_depth = 0

    def subscribe(self, callback):
        """
        Subscribe a callback to undo/redo events.
        Args:
            callback (callable): Function to call on undo/redo events.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _notify(self, event_type):
        """
        Notify all subscribed callbacks of an event.
        Args:
            event_type (str): The type of event ('undo', 'redo', etc.).
        """
        for cb in self._callbacks:
            try:
                cb(event_type)
            except Exception as e:
                # ...removed debug print...
                pass

    def push(self, command: BaseCommand):
        """
        Push a command onto the undo stack and execute it.
        Args:
            command (BaseCommand): The command to execute and push.
        """
        self.do(command)

    def do(self, command: BaseCommand):
        """
        Execute a command and add it to the undo stack or current transaction.
        Args:
            command (BaseCommand): The command to execute.
        """
        command.execute()
        command.mark_executed()
        if self.in_transaction():
            self._transaction_commands.append(command)
        else:
            self._undo_stack.append(command)
            self._redo_stack.clear()


# TransactionCommand groups multiple commands as a single undoable/redoable action
class TransactionCommand(BaseCommand):
    """
    Groups multiple commands as a single undoable/redoable action for transactions.
    """
    def __init__(self, commands, description=None):
        """
        Initialize the TransactionCommand with a list of commands and optional description.
        Args:
            commands (list): List of BaseCommand objects.
            description (str): Optional description for the transaction.
        """
        super().__init__(description or "Transaction")
        self.commands = list(commands)

    def execute(self):
        """
        Execute all commands in the transaction.
        """
        for cmd in self.commands:
            cmd.execute()

    def undo(self):
        """
        Undo all commands in the transaction in reverse order.
        """
        for cmd in reversed(self.commands):
            cmd.undo()

    def redo(self):
        """
        Redo all commands in the transaction in order.
        """
        for cmd in self.commands:
            cmd.redo()

    def undo(self):
        """
        Undo the last command on the undo stack.
        """
        if not self._undo_stack:
            return
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self._notify('undo')

    def redo(self):
        """
        Redo the last undone command on the redo stack.
        """
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)
        self._notify('redo')

    def clear(self):
        """
        Clear both the undo and redo stacks.
        """
        self._undo_stack.clear()
        self._redo_stack.clear()

    def can_undo(self):
        """
        Return True if there are commands to undo.
        """
        return bool(self._undo_stack)

    def can_redo(self):
        """
        Return True if there are commands to redo.
        """
        return bool(self._redo_stack)

    @property
    def undo_stack(self):
        """
        Return the current undo stack.
        """
        return list(self._undo_stack)

    @property
    def redo_stack(self):
        """
        Return the current redo stack.
        """
        return list(self._redo_stack)

    def __len__(self):
        """
        Return the number of commands in the undo stack.
        """
        return len(self._undo_stack)

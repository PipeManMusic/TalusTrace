import pytest
from unittest.mock import MagicMock

# Simulate a command class
class DummyCommand:
    executed_via_dispatcher = False
    def __init__(self, *a, **k):
        self.executed = False
    def execute(self):
        self.executed = True
        DummyCommand.executed_via_dispatcher = True

# Simulate a registry and dispatcher
class DummyRegistry:
    def __init__(self):
        self.actions = {}
    def register(self, action_id, handler):
        self.actions[action_id] = handler
    def execute(self, action_id, context=None, **flags):
        return self.actions[action_id](context, **flags)

def dispatch_action(action_id, context=None, registry=None, **flags):
    assert registry is not None, "Registry must be provided"
    return registry.execute(action_id, context, **flags)

# Simulate a UI or other code that might bypass the dispatcher

def test_command_must_use_dispatcher(monkeypatch):
    """
    This test fails if DummyCommand is executed directly, not via dispatch_action.
    """
    registry = DummyRegistry()
    def delete_action(context, **flags):
        cmd = DummyCommand()
        cmd.execute()
        return cmd
    registry.register("edit.delete", delete_action)
    # Simulate bypass: direct command execution (should fail)
    DummyCommand.executed_via_dispatcher = False
    cmd = DummyCommand()
    cmd.execute()
    assert not DummyCommand.executed_via_dispatcher, "Command was executed directly, not via dispatcher!"
    # Now use dispatcher (should pass)
    DummyCommand.executed_via_dispatcher = False
    dispatch_action("edit.delete", None, registry=registry)
    assert DummyCommand.executed_via_dispatcher, "Command was not executed via dispatcher!"

def test_all_commands_registered(monkeypatch):
    """
    This test fails if a command is not registered in the dispatcher registry.
    """
    registry = DummyRegistry()
    # Only register one action
    registry.register("edit.delete", lambda ctx, **f: DummyCommand())
    # Simulate a list of all required commands
    required_commands = ["edit.delete", "edit.add", "edit.update"]
    missing = [cmd for cmd in required_commands if cmd not in registry.actions]
    assert not missing, f"Missing commands in dispatcher registry: {missing}"

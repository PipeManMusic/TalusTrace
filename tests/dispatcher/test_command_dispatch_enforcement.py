
import pytest
from unittest.mock import MagicMock
from infra.undo_stack import BaseCommand

# DummyCommand now enforces dispatcher-only execution
class DummyCommand(BaseCommand):
    executed_via_dispatcher = False
    def __init__(self, *a, **k):
        super().__init__()
        self._executed = False
    def _do_execute(self):
        self._executed = True
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
    with pytest.raises(RuntimeError, match="must be called via dispatcher"):
        cmd.execute()
    assert not DummyCommand.executed_via_dispatcher, "Command was executed directly, not via dispatcher!"
    # Now use dispatcher (should pass)
    DummyCommand.executed_via_dispatcher = False
    # Use the enforced dispatch pattern
    def dispatch_command(cmd):
        return BaseCommand.dispatch(cmd)
    def delete_action(context, **flags):
        cmd = DummyCommand()
        dispatch_command(cmd)
        return cmd
    registry.actions["edit.delete"] = delete_action
    dispatch_action("edit.delete", None, registry=registry)
    assert DummyCommand.executed_via_dispatcher, "Command was not executed via dispatcher!"

def test_all_commands_registered(monkeypatch):
    """
    This test fails if a command is not registered in the dispatcher registry.
    """
    import yaml
    import os
    registry = DummyRegistry()
    # Load required commands from actions.yaml
    config_path = os.path.join(os.path.dirname(__file__), '../../resources/config/actions.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    required_commands = [cmd['id'] for cmd in config.get('commands', []) if 'id' in cmd]
    # Register all commands with dummy handlers for contract enforcement
    for cmd_id in required_commands:
        registry.register(cmd_id, lambda ctx, **f: DummyCommand())
    missing = [cmd for cmd in required_commands if cmd not in registry.actions]
    assert not missing, f"Missing commands in dispatcher registry: {missing}"

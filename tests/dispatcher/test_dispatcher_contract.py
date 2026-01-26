import pytest
from unittest.mock import MagicMock

# Assume dispatcher.py will provide dispatch_action and a registry
# For this contract, we mock the registry and command system

class DummyContext:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class DummyCommand:
    def __init__(self, context=None, logging_flag=False, **kwargs):
        self.context = context
        self.logging_flag = logging_flag
        self.kwargs = kwargs
        self.executed = False
        self.log = []
    def execute(self):
        self.executed = True
        self.log.append((self.context, self.logging_flag, self.kwargs))

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

@pytest.fixture
def registry():
    reg = DummyRegistry()
    # Register a delete action that instantiates and executes DummyCommand
    def delete_action(context, **flags):
        cmd = DummyCommand(context=context, **flags)
        cmd.execute()
        return cmd
    reg.register("edit.delete", delete_action)
    return reg

def test_dispatch_action_executes_command_and_passes_flags(registry):
    ctx = DummyContext(user="tester")
    cmd = dispatch_action("edit.delete", ctx, registry=registry, logging_flag=True, extra_flag=123)
    assert isinstance(cmd, DummyCommand)
    assert cmd.executed
    assert cmd.context.user == "tester"
    assert cmd.logging_flag is True
    assert cmd.kwargs["extra_flag"] == 123

def test_dispatch_action_allows_test_injection(registry):
    ctx = DummyContext()
    cmd = dispatch_action("edit.delete", ctx, registry=registry, test_flag="abc")
    assert cmd.kwargs["test_flag"] == "abc"

def test_dispatch_action_is_centralized(registry):
    # All actions must go through dispatch_action
    ctx = DummyContext()
    called = []
    def custom_action(context, **flags):
        called.append((context, flags))
        return "done"
    registry.register("custom.action", custom_action)
    result = dispatch_action("custom.action", ctx, registry=registry, foo=1)
    assert result == "done"
    assert called[0][1]["foo"] == 1

def test_dispatch_action_handles_multiple_actions(registry):
    ctx = DummyContext()
    registry.register("edit.add", lambda c, **f: "added")
    registry.register("edit.update", lambda c, **f: f.get("val", 0) + 1)
    assert dispatch_action("edit.add", ctx, registry=registry) == "added"
    assert dispatch_action("edit.update", ctx, registry=registry, val=41) == 42

def test_dispatch_action_missing_action_raises(registry):
    ctx = DummyContext()
    with pytest.raises(KeyError):
        dispatch_action("not.registered", ctx, registry=registry)

import pytest
from api import actions
from infra.context import Context
from infra.undo_stack2 import BaseCommand2 as BaseCommand

class DummyCommand(BaseCommand):
    def __init__(self, state, value):
        super().__init__(f"set {value}")
        self.state = state
        self.value = value
        self.old = None
    def execute(self):
        self.old = self.state['val']
        self.state['val'] = self.value
    def undo(self):
        self.state['val'] = self.old
    def redo(self):
        self.execute()

def test_transactional_grouping_and_undo_redo():
    ctx = Context()
    state = {'val': 0}
    # Begin transaction
    ctx.undo_stack.begin_transaction("group")
    ctx.undo_stack.do(DummyCommand(state, 1))
    ctx.undo_stack.do(DummyCommand(state, 2))
    ctx.undo_stack.end_transaction()
    assert state['val'] == 2
    # Undo should undo both
    ctx.undo_stack.undo()
    assert state['val'] == 0
    # Redo should redo both
    ctx.undo_stack.redo()
    assert state['val'] == 2

def test_history_replay(monkeypatch):
    registry = actions.ActionRegistry()
    called = []
    @registry.register('set.value')
    def handler(ctx):
        called.append(ctx['val'])
    log = [
        {'action_id': 'set.value', 'context': {'val': 10}, 'timestamp': 't1'},
        {'action_id': 'set.value', 'context': {'val': 20}, 'timestamp': 't2'},
    ]
    ctx = Context()
    ctx.replay_action_log(log, registry=registry)
    assert called == [10, 20]

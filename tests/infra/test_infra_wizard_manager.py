import pytest
from infra.wizard_manager import WizardManager

def test_wizard_manager_basic():
    steps = ['a', 'b', 'c']
    wiz = WizardManager(steps)
    wiz.start()
    assert wiz.active
    assert wiz.current == 0
    wiz.set_data('a', {'foo': 1})
    assert wiz.get_data('a')['foo'] == 1
    wiz.next()
    assert wiz.current == 1
    wiz.prev()
    assert wiz.current == 0
    wiz.next(); wiz.next()
    assert not wiz.active  # Finished

def test_wizard_manager_serialize():
    steps = ['x', 'y']
    wiz = WizardManager(steps)
    wiz.start()
    wiz.set_data('x', {'bar': 2})
    wiz.next()
    state = wiz.serialize()
    wiz2 = WizardManager.deserialize(state)
    assert wiz2.steps == steps
    assert wiz2.current == 1
    assert wiz2.get_data('x')['bar'] == 2
    assert wiz2.active == wiz.active

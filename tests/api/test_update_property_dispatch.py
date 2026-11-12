"""Regression tests for the pin/property edit freeze.

Editing a single property must dispatch exactly one ``model_changed`` event.
A previous implementation dispatched it twice (once from
``UpdatePropertyCommand.execute`` and again from ``APIManager.update_property``),
which doubled every subscriber's work (full audit + property-panel rebuild)
and froze the UI on a single field edit.
"""
import uuid

from api.manager import APIManager
from infra.context import Context
from core.device import Device


def _fresh_api():
    APIManager._instance = None
    ctx = Context()
    return APIManager.get_instance(context=ctx), ctx


def test_update_property_dispatches_model_changed_once():
    api, ctx = _fresh_api()
    device = Device(id=str(uuid.uuid4()), x=0, y=0, meta={"label": "A"})
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))

    calls = []
    api.subscribe("model_changed", lambda data=None: calls.append(data))

    api.update_property(device, "meta.label", "B")

    assert device.meta["label"] == "B"
    assert len(calls) == 1, f"expected exactly one model_changed, got {len(calls)}"


def test_undo_redo_dispatches_model_changed_once_each():
    api, ctx = _fresh_api()
    device = Device(id=str(uuid.uuid4()), x=5, y=5)
    from api.commands.device import AddDeviceCommand
    ctx.undo_stack.push(AddDeviceCommand(device))

    api.update_property(device, "x", 42)

    calls = []
    api.subscribe("model_changed", lambda data=None: calls.append(data))

    ctx.undo_stack.undo()
    assert device.x == 5
    assert len(calls) == 1

    calls.clear()
    ctx.undo_stack.redo()
    assert device.x == 42
    assert len(calls) == 1

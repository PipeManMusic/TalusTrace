import json

import pytest

from talustrace.frontend import items_baseline as ib


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    # Redirect configure.json to a temp path and clear in-memory counters
    cfg = tmp_path / "configure.json"
    monkeypatch.setattr(ib, "CONFIG_PATH", cfg)
    ib._ACTION_USAGE.clear()
    yield
    ib._ACTION_USAGE.clear()


def test_usage_persistence_roundtrip(tmp_path, monkeypatch):
    cfg = tmp_path / "configure.json"
    monkeypatch.setattr(ib, "CONFIG_PATH", cfg)
    ib._ACTION_USAGE.clear()

    ib._record_action_usage("device.edit")
    ib._record_action_usage("device.edit")
    ib._record_action_usage("pin.edit")

    # Data is written to configure.json
    data = json.loads(cfg.read_text())
    usage = data.get(ib.CONFIG_USAGE_KEY, {})
    assert usage["device.edit"] == 2
    assert usage["pin.edit"] == 1

    # Clear and reload to confirm persistence is honored
    ib._ACTION_USAGE.clear()
    ib._load_usage()
    assert ib._ACTION_USAGE["device.edit"] == 2
    assert ib._ACTION_USAGE["pin.edit"] == 1


def test_usage_sorting_order(tmp_path, monkeypatch):
    cfg = tmp_path / "configure.json"
    monkeypatch.setattr(ib, "CONFIG_PATH", cfg)
    ib._ACTION_USAGE.clear()

    # Simulate usage counts: C most, A next, B untouched
    ib._record_action_usage("action.a")
    ib._record_action_usage("action.c")
    ib._record_action_usage("action.c")

    entries = [
        ("action.a", "A", None),
        ("action.b", "B", None),
        ("action.c", "C", None),
    ]

    ordering = [e[0] for e in sorted(entries, key=lambda e: (-ib._usage_rank(e[0]), entries.index(e)))]
    assert ordering == ["action.c", "action.a", "action.b"]

import pytest
from pathlib import Path
from infra.action_logger import ActionLogger

def test_action_logger_round_trip(tmp_path):
    log_path = tmp_path / "actions.log"
    logger = ActionLogger(log_path)

    logger.log("undo", {"desc": "Undo test"})
    logger.log("redo", {"desc": "Redo test"})
    logger.log("custom", {"foo": 123})

    events = list(logger.read_log())
    assert len(events) == 3
    assert events[0]["event_type"] == "undo"
    assert events[1]["event_type"] == "redo"
    assert events[2]["payload"]["foo"] == 123

    # Test filter
    redo_events = list(logger.filter_events("redo"))
    assert len(redo_events) == 1
    assert redo_events[0]["event_type"] == "redo"

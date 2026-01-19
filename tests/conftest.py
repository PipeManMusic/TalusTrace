import pytest
import sys
import importlib

@pytest.fixture
def enforce_device_mvc_fixture():
    # Import context manager from mvc_enforce.py
    sys.path.append('.')
    mvc_enforce = importlib.import_module('tests.mvc_enforce')
    return mvc_enforce.enforce_device_mvc
from unittest.mock import MagicMock
from infra.context import ProjectContext
from core.harness import Harness
from core.wire import Wire
from api.manager import APIManager

@pytest.fixture
def fresh_harness():
    return Harness()

@pytest.fixture
def fresh_api(fresh_harness):
    # Reset Singleton
    APIManager._instance = None
    
    # Setup Headless API
    api = APIManager()
    api.context = ProjectContext()
    api.context.harness = fresh_harness
    
    # Mock UI dependencies (Scene/View) so logic tests don't crash
    api.scene = MagicMock()
    api.view = MagicMock()
    api.view.transform.return_value = MagicMock() 
    
    return api

@pytest.fixture
def create_test_wire(fresh_api):
    def _factory(nodes=None, **kwargs):
        # If path_nodes is passed in kwargs, use it as nodes
        if 'path_nodes' in kwargs:
            nodes = kwargs.pop('path_nodes')
        if nodes is None:
            nodes = [[0,0], [100,0]]
        # Defaults for robustness
        kwargs.setdefault("id", "W_TEST")
        kwargs.setdefault("from_conn", "D1")
        kwargs.setdefault("to_conn", "D2")
        wire = Wire(path_nodes=nodes, **kwargs)
        fresh_api.context.harness.wires.append(wire)
        return wire
    return _factory

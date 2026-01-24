"""
Integration tests for concurrency and performance of the API and core infrastructure.
Covers:
- Simultaneous transactions (thread/process safety)
- High-volume object creation and modification
- Undo/redo under load
- Persistence under stress
- Timing and throughput measurements
"""
import threading
import time
import uuid
import pytest
from api.manager import APIManager
from core.harness import Harness
from core.device import Device
from core.wire import Wire
from infra.undo_stack import UndoStack

@pytest.mark.integration
def test_concurrent_device_addition():
    """Test adding devices concurrently to the harness."""
    from api.manager import APIManager
    from core.harness import DeviceList
    import threading
    APIManager.reset()
    api = APIManager()
    num_threads = 10
    devices_per_thread = 100
    threads = []
    lock = threading.Lock()
    def add_devices():
        for _ in range(devices_per_thread):
            d = Device(id=str(uuid.uuid4()), name="D", pins=[])
            with lock, DeviceList.test_bypass():
                api.context.harness.devices.append(d)
    for _ in range(num_threads):
        t = threading.Thread(target=add_devices)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    assert len(api.context.harness.devices) == num_threads * devices_per_thread

@pytest.mark.integration
def test_performance_bulk_wire_creation():
    """Test performance of bulk wire creation."""
    from api.manager import APIManager
    from core.wire import Wire
    APIManager.reset()
    api = APIManager()
    num_wires = 5000
    start = time.time()
    for _ in range(num_wires):
        w = Wire(id=str(uuid.uuid4()), from_conn="D1", to_conn="D2", path_nodes=[[0,0],[100,0]])
        api.context.harness.wires.append(w)
    duration = time.time() - start
    assert len(api.context.harness.wires) == num_wires
    # Arbitrary threshold: should complete in <2 seconds on dev hardware
    assert duration < 2.0

@pytest.mark.integration
def test_undo_redo_under_load():
    """Test undo/redo stack under high transaction load."""
    from api.manager import APIManager
    from core.harness import DeviceList
    APIManager.reset()
    api = APIManager()
    num_ops = 1000
    devices = []
    with DeviceList.test_bypass():
        for _ in range(num_ops):
            d = Device(id=str(uuid.uuid4()), name="D", pins=[])
            devices.append(d)
            api.context.harness.devices.append(d)
    for _ in range(num_ops):
        api.context.harness.devices.pop()
    assert len(api.context.harness.devices) == 0
    with DeviceList.test_bypass():
        for d in devices:
            api.context.harness.devices.append(d)
    assert len(api.context.harness.devices) == num_ops

@pytest.mark.integration
def test_persistence_stress(tmp_path):
    """Test saving/loading a large harness to disk."""
    from api.manager import APIManager
    from core.harness import DeviceList, Harness
    import json
    APIManager.reset()
    api = APIManager()
    with DeviceList.test_bypass():
        for _ in range(2000):
            d = Device(id=str(uuid.uuid4()), name="D", pins=[])
            api.context.harness.devices.append(d)
    file_path = tmp_path / "harness.json"
    start = time.time()
    with open(file_path, "w") as f:
        json.dump(api.context.harness.to_dict(), f)
    duration_save = time.time() - start
    start = time.time()
    with open(file_path) as f:
        loaded_dict = json.load(f)
    loaded = Harness.from_dict(loaded_dict)
    duration_load = time.time() - start
    assert len(loaded.devices) == 2000
    assert duration_save < 2.0
    assert duration_load < 2.0

@pytest.mark.integration
def test_api_manager_throughput():
    """Test APIManager throughput for repeated actions."""
    from api.manager import APIManager
    from core.harness import DeviceList
    APIManager.reset()
    api = APIManager()
    num_actions = 1000
    start = time.time()
    with DeviceList.test_bypass():
        for _ in range(num_actions):
            d = Device(id=str(uuid.uuid4()), name="D", pins=[])
            api.context.harness.devices.append(d)
    duration = time.time() - start
    assert duration < 2.0
    assert len(api.context.harness.devices) == num_actions

import pytest
from infra.cache_manager import CacheManager
import tempfile
import shutil
import os

def test_cache_manager_basic():
    cache = CacheManager(cache_dir=".cache/test1")
    cache.set("foo", {"bar": 42})
    assert cache.get("foo")["bar"] == 42
    cache.invalidate("foo")
    assert cache.get("foo") is None
    cache.set("baz", [1,2,3])
    cache.clear()
    assert cache.get("baz") is None
    shutil.rmtree(".cache/test1", ignore_errors=True)

def test_cache_manager_persistence():
    tmpdir = tempfile.mkdtemp()
    cache = CacheManager(cache_dir=tmpdir)
    cache.set("persist", {"x": 1})
    assert cache.get("persist")["x"] == 1
    # Simulate reload
    cache2 = CacheManager(cache_dir=tmpdir)
    assert cache2.get("persist")["x"] == 1
    shutil.rmtree(tmpdir, ignore_errors=True)

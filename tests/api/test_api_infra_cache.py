import pytest
from api.manager import APIManager
from infra.context import Context
from core.device import Device

# Test: API can use cache via infra

def test_api_cache_manager():
    from infra.cache_manager import CacheManager
    cache = CacheManager(cache_dir=".cache/api_test")
    cache.save("foo", 123)
    assert cache.load("foo") == 123
    cache.save("bar", "baz")
    assert cache.load("bar") == "baz"
    import os
    os.remove(cache.cache_dir / "foo.bin")
    os.remove(cache.cache_dir / "bar.bin")

"""
CacheManager: System cache for binary blobs (msgpack or pickle) in Talus Trace.
Handles saving, loading, invalidating, and clearing cached data for fast rendering and persistence.
"""
import pickle
import os
from pathlib import Path

class CacheManager:
    """PH5-CLN.2: System Cache for binary blobs (msgpack or pickle)."""
    
    def __init__(self, cache_dir=".cache/render"):
        """
        Initialize the CacheManager with a cache directory.
        Args:
            cache_dir (str): Path to the cache directory.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


    def save(self, key, data):
        """Saves data to a binary blob."""
        path = self.cache_dir / f"{key}.bin"
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, key):
        """Retrieves cached data for sub-millisecond rendering."""
        path = self.cache_dir / f"{key}.bin"
        if path.exists():
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None

    def invalidate(self, key):
        """Remove a specific cache entry."""
        path = self.cache_dir / f"{key}.bin"
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass

    def clear(self):
        """Clear all cache entries."""
        for file in self.cache_dir.glob("*.bin"):
            try:
                file.unlink()
            except Exception:
                pass

    def set(self, key, data):
        """Alias for save, for in-memory style API."""
        self.save(key, data)

    def get(self, key):
        """Alias for load, for in-memory style API."""
        return self.load(key)
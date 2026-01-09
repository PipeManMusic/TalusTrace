import pickle
import os
from pathlib import Path

class CacheManager:
    """PH5-CLN.2: System Cache for binary blobs (msgpack or pickle)."""
    
    def __init__(self, cache_dir=".cache/render"):
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
            with open(path, "rb") as f:
                return pickle.load(f)
        return None
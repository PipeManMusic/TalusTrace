"""Test utilities for shared mocks and constants."""

class MutationDetectList(list):
    """List wrapper that flips a flag when mutated (append, setitem, etc.)."""

    def __init__(self, iterable, flag_store, flag_key):
        super().__init__(iterable or [])
        self._flag_store = flag_store
        self._flag_key = flag_key

    def _mark(self):
        self._flag_store[self._flag_key] = True

    def __setitem__(self, key, value):
        self._mark()
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        self._mark()
        return super().__delitem__(key)

    def append(self, value):
        self._mark()
        return super().append(value)

    def extend(self, value):
        self._mark()
        return super().extend(value)

    def insert(self, index, value):
        self._mark()
        return super().insert(index, value)

    def pop(self, index=-1):
        self._mark()
        return super().pop(index)

    def remove(self, value):
        self._mark()
        return super().remove(value)

    def clear(self):
        self._mark()
        return super().clear()

    def __iadd__(self, value):
        self._mark()
        return super().__iadd__(value)

    def __imul__(self, value):
        self._mark()
        return super().__imul__(value)


class TEST_UUIDS:
    """Stable UUID constants for tests."""
    DELETE = "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b"

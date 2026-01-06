"""Small façade module to expose TwistedBundle functionality for standalone use and testing.
This file intentionally wraps the existing TwistedBundleItem implementation so we can
start developing a stable public interface while keeping the original implementation
in `items_baseline` until a full refactor is done.
"""

from .items_baseline import TwistedBundleItem as _TwistedBundleItemImpl


class TwistedBundleItem(_TwistedBundleItemImpl):
    """Facade subclass of the original TwistedBundleItem.

    This class exists to provide a stable import path for tests and to make it
    easy to eventually move/replace the implementation without touching code
    that imports this class.
    """

    pass


__all__ = ["TwistedBundleItem"]

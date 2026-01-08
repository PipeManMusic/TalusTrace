from ui.items import TwistedPairItem
from unittest.mock import MagicMock

def test_twisted_pair_lod_switching():
    """
    Validates PH3-2.2: UI: Twisted Pair LOD Switcher.
    Ensures rendering swaps between HELIX and HATCH based on view scale.
    """
    path = [(0.0, 0.0), (100.0, 0.0)]

    # FIX: No transformer argument needed for instantiation
    tp_item = TwistedPairItem(path_nodes=path)

    # Validate LOD logic directly
    # Scale > 0.5 -> HELIX
    assert tp_item.determine_lod(1.0) == "HELIX"
    
    # Scale < 0.5 -> HATCH
    assert tp_item.determine_lod(0.1) == "HATCH"
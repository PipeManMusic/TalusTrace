import pytest
from unittest.mock import MagicMock
from ui.items import TwistedPairItem

def test_twisted_pair_lod_switching():
    """
    Validates PH3-2.2: UI: Twisted Pair LOD Switcher.
    Ensures rendering swaps between HELIX and HATCH based on view scale.
    """
    # Threshold usually comes from theme_tokens.json (e.g., 0.5)
    lod_threshold = 0.5
    
    # Mock a transformer and theme
    mock_transformer = MagicMock()
    mock_theme = MagicMock()
    mock_theme.get_dimension.return_value = lod_threshold
    
    mock_transformer.mm_to_px.return_value = 1.0
    mock_transformer.mm_to_px_tuple.return_value = (0.0, 0.0)
    
    path = [(0.0, 0.0), (100.0, 0.0)]
    
    # Updated signature: (path_nodes, transformer)
    tp_item = TwistedPairItem(path_nodes=path, transformer=mock_transformer)
    
    # Test Case 1: High Zoom (Close up) -> Expect High Fidelity Helix
    # In Qt, m11() represents the horizontal scaling factor
    assert tp_item.determine_lod(view_scale=1.0) == "HELIX"
    
    # Test Case 2: Low Zoom (Far away) -> Expect Performance Hatch
    assert tp_item.determine_lod(view_scale=0.1) == "HATCH"
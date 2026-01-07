import pytest
from core.geometry import generate_helix_points

def test_helix_sine_wave_generation():
    """
    Validates PH3-2.1: UI: Procedural Helix Sine Wave Logic.
    Ensures offset points are generated along the normal of a path.
    """
    # Simple straight path from (0,0) to (10,0)
    base_path = [(0.0, 0.0), (10.0, 0.0)]
    
    # Generate points for Helix A and Helix B
    helix_a, helix_b = generate_helix_points(base_path, amplitude=2.0, pitch=5.0)
    
    # At t=0, sine wave is at 0, so y-offset should be near 0
    assert helix_a[0][1] == pytest.approx(0.0, 0.1)
    
    # At t=pitch/4 (1.25mm), sine wave is at peak, y-offset should be amplitude
    # (Checking if the sine wave logic is producing expected oscillation)
    peak_y = [p[1] for p in helix_a if 1.0 <= p[0] <= 1.5]
    assert max(peak_y) == pytest.approx(2.0, 0.1)

def test_lod_switcher_logic():
    """
    Validates PH3-2.2: UI: Twisted Pair LOD Switcher.
    Swaps rendering based on lod_threshold_scale.
    """
    from ui.items import TwistedPairItem
    
    # Mock zoom scale
    high_detail_zoom = 2.0  # Zoomed in
    low_detail_zoom = 0.2   # Zoomed out
    
    tp_item = TwistedPairItem()
    
    # Should use Helix (High Detail)
    assert tp_item.determine_lod(high_detail_zoom) == "HELIX"
    
    # Should use Hatch (Low Detail)
    assert tp_item.determine_lod(low_detail_zoom) == "HATCH"
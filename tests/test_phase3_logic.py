import pytest
from core.geometry import generate_helix_points

def test_helix_sine_wave_offsets_robust():
    """
    Validates PH3-2.1: Procedural Helix Sine Wave Logic.
    Uses high sampling density to ensure peaks are captured for amplitude validation.
    """
    path = [(0, 0), (100, 0)]  # 100mm horizontal path
    amplitude = 2.0
    pitch = 10.0
    
    # Increase num_points to 1000 to ensure the peaks (±2.0) are sampled
    helix_a, helix_b = generate_helix_points(
        path, 
        pitch=pitch, 
        amplitude=amplitude, 
        num_points=1000
    )
    
    # Extract y-values (offsets for a horizontal path)
    y_values_a = [p[1] for p in helix_a]
    
    # Verify oscillation reaches the expected amplitude within a tight tolerance
    assert max(y_values_a) == pytest.approx(amplitude, abs=0.01)
    assert min(y_values_a) == pytest.approx(-amplitude, abs=0.01)
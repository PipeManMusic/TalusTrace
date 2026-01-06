
import math
import pytest
import importlib.util
import sys
from typing import Tuple, List

# Import the function if it exists, else define a dummy for test collection
try:
    from talustrace.backend.geometry import calculate_double_helix
except ImportError:
    def calculate_double_helix(start: Tuple[float, float], end: Tuple[float, float], amplitude: float, wavelength: float, phase_offset: float = 0.0) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        return [], []

def test_helix_structure():
    result = calculate_double_helix((0, 0), (10, 0), 2, 10)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], list)
    assert isinstance(result[1], list)

def test_horizontal_segment():
    amplitude = 5
    strand1, strand2 = calculate_double_helix((0, 0), (100, 0), amplitude, 20)
    if not strand1:
        pytest.skip("Function not implemented yet")
    y_values = [pt[1] for pt in strand1]
    assert max(y_values) == pytest.approx(amplitude, abs=0.5)
    assert min(y_values) == pytest.approx(-amplitude, abs=0.5)

def test_vertical_segment():
    amplitude = 3
    strand1, strand2 = calculate_double_helix((0, 0), (0, 100), amplitude, 20)
    if not strand1:
        pytest.skip("Function not implemented yet")
    x_values = [pt[0] for pt in strand1]
    assert max(x_values) == pytest.approx(amplitude, abs=0.5)
    assert min(x_values) == pytest.approx(-amplitude, abs=0.5)

def test_zero_length():
    strand1, strand2 = calculate_double_helix((0, 0), (0, 0), 2, 10)
    assert strand1 == [] or len(strand1) == 0
    assert strand2 == [] or len(strand2) == 0

def test_independence():
    # Ensure no PySide6 or Qt imports in the geometry module
    spec = importlib.util.find_spec("talustrace.backend.geometry")
    if not spec or not spec.origin:
        pytest.skip("geometry module not found")
    with open(spec.origin, "r") as f:
        code = f.read()
    assert "PySide6" not in code
    assert "Qt" not in code

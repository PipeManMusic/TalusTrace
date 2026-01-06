import pytest
from typing import Tuple, List

# Import will fail until implemented, as intended for TDD
from talustrace.backend.geometry import calculate_double_helix

def test_standard_line():
    start = (0.0, 0.0)
    end = (100.0, 0.0)
    amplitude = 10.0
    wavelength = 20.0
    strand_1, strand_2 = calculate_double_helix(start, end, amplitude, wavelength)
    assert isinstance(strand_1, list)
    assert isinstance(strand_2, list)
    assert len(strand_1) > 10
    assert len(strand_2) > 10

def test_zero_length():
    start = (0.0, 0.0)
    end = (0.0, 0.0)
    amplitude = 10.0
    wavelength = 20.0
    strand_1, strand_2 = calculate_double_helix(start, end, amplitude, wavelength)
    assert strand_1 == [] or len(strand_1) == 0
    assert strand_2 == [] or len(strand_2) == 0

def test_amplitude_check():
    start = (0.0, 0.0)
    end = (100.0, 0.0)
    amplitude = 10.0
    wavelength = 20.0
    strand_1, strand_2 = calculate_double_helix(start, end, amplitude, wavelength)
    y_values_1 = [pt[1] for pt in strand_1]
    y_values_2 = [pt[1] for pt in strand_2]
    assert max(y_values_1) <= amplitude + 1.0
    assert min(y_values_1) >= -amplitude - 1.0
    assert max(y_values_2) <= amplitude + 1.0
    assert min(y_values_2) >= -amplitude - 1.0

def test_no_qt_imports():
    import sys
    assert 'PySide6' not in sys.modules
    assert 'Qt' not in sys.modules

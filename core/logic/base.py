"""
Base logic for Talus Trace.
Provides base classes and utilities for logic modules.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Iterator, Any

@dataclass
class ComplianceViolation:
    """
    Standardized return object for all Engineering Rules.
    Replaces ad-hoc dictionaries.
    """
    category: str  # e.g., "STIFFNESS", "BEND_RADIUS"
    severity: str  # e.g., "WARNING", "ERROR"
    message: Optional[str] = None
    value: Optional[float] = None
    indices: Optional[List[int]] = None
    
    def to_dict(self):
        """
        Serialize the base logic object to a dictionary.
        Returns:
            dict: Dictionary representation of the object.
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}

def iter_segments(nodes: List[Tuple[float, float]]) -> Iterator[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Generator that yields consecutive point pairs (segments) from a path.
    Used by Layout, Bundling, and Geometry logic.
    """
    if not nodes or len(nodes) < 2:
        return
    for i in range(len(nodes) - 1):
        yield nodes[i], nodes[i+1]
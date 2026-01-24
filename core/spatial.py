"""
Spatial module for Talus Trace.
Provides spatial management, grid snapping, and spatial hashing utilities.
"""

class SpatialManager:
    """
    Manages spatial grid and snapping operations for device placement.
    """
    def __init__(self):
        """
        Initialize the spatial manager with default grid size and snapping enabled.
        """
        self.grid_size = 25.0
        self.snap_enabled = True

    def snap(self, point: tuple) -> tuple:
        """Snaps a (x, y) tuple to the nearest grid point. Returns a tuple."""
        x0, y0 = point
        if not self.snap_enabled:
            return (x0, y0)
        g = self.grid_size
        x = round(x0 / g) * g
        y = round(y0 / g) * g
        return (x, y)
from collections import defaultdict
from typing import Tuple, List, Dict, Any
import math

class SpatialHash:
    """
    Spatial hash for efficient spatial queries and object indexing.
    """
    def __init__(self, cell_size: float = 10.0):
        """
        Initialize the spatial hash with a given cell size.
        Args:
            cell_size (float): Size of each cell in the hash grid.
        """
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], List[Tuple[Any, Tuple[float, float]]]] = defaultdict(list)

    def _cell_coords(self, point: Tuple[float, float]) -> Tuple[int, int]:
        """
        Compute cell coordinates for a given point.
        Args:
            point (Tuple[float, float]): The (x, y) coordinates.
        Returns:
            Tuple[int, int]: Cell coordinates in the grid.
        """
        x, y = point
        return (int(math.floor(x / self.cell_size)), int(math.floor(y / self.cell_size)))

    def insert(self, obj_id: Any, point: Tuple[float, float]):
        """
        Insert an object into the spatial hash at the given point.
        Args:
            obj_id (Any): Identifier for the object.
            point (Tuple[float, float]): The (x, y) coordinates.
        """
        cell = self._cell_coords(point)
        self.cells[cell].append((obj_id, point))

    def query_radius(self, center: Tuple[float, float], radius: float) -> List[Any]:
        """
        Query all objects within a given radius from the center point.
        Args:
            center (Tuple[float, float]): Center coordinates.
            radius (float): Search radius.
        Returns:
            List[Any]: List of object IDs within the radius.
        """
        cx, cy = center
        min_cell = self._cell_coords((cx - radius, cy - radius))
        max_cell = self._cell_coords((cx + radius, cy + radius))
        result = []
        r2 = radius * radius
        for ix in range(min_cell[0], max_cell[0] + 1):
            for iy in range(min_cell[1], max_cell[1] + 1):
                for obj_id, pt in self.cells.get((ix, iy), []):
                    dx = pt[0] - cx
                    dy = pt[1] - cy
                    if dx * dx + dy * dy <= r2:
                        result.append(obj_id)
        return result

from collections import defaultdict
from typing import Tuple, List, Dict, Any
import math

class SpatialHash:
    def __init__(self, cell_size: float = 10.0):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], List[Tuple[Any, Tuple[float, float]]]] = defaultdict(list)

    def _cell_coords(self, point: Tuple[float, float]) -> Tuple[int, int]:
        x, y = point
        return (int(math.floor(x / self.cell_size)), int(math.floor(y / self.cell_size)))

    def insert(self, obj_id: Any, point: Tuple[float, float]):
        cell = self._cell_coords(point)
        self.cells[cell].append((obj_id, point))

    def query_radius(self, center: Tuple[float, float], radius: float) -> List[Any]:
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

from typing import List, Tuple

class Router:
    """
    Calculates wire paths using 'Rubber Band' logic (Elbows).
    """
    @staticmethod
    def route_wire(start: Tuple[float, float], end: Tuple[float, float], elbows: List[Tuple[float, float]] = None) -> List[Tuple[float, float]]:
        """
        Returns a list of points representing the wire path.
        Currently just a straight line or simple elbows.
        """
        path = [start]
        if elbows:
            path.extend(elbows)
        path.append(end)
        return path

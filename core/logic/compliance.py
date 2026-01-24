"""
Compliance logic for Talus Trace.
Implements rules and checks for PH4 compliance.
"""

import math
from typing import List, Optional, Dict, Any
from .bundling import calculate_bundle_diameter
from .base import ComplianceViolation

# PH3-3.1: Engineering Rule for Bundle Stiffness
def check_bundle_constraints(wire_diameters: List[float]) -> Optional[ComplianceViolation]:
    """
    Core engineering rule for bundle stiffness (Spec 7).
    Standard Rule: Bundles > 40mm are too stiff for Bronco II routing.
    """
    diameter = calculate_bundle_diameter(wire_diameters)
    if diameter > 40.0:
        return ComplianceViolation(
            category="STIFFNESS",
            severity="WARNING",
            value=diameter,
            message=f"Bundle diameter ({diameter:.2f}mm) exceeds 40mm flexible limit."
        )
    return None

def check_bend_radius_violations(path_nodes, wire_diameter, min_bend_factor=4.0) -> Optional[ComplianceViolation]:
    """
    Checks each wire segment for bend radius violations.
    Returns None if compliant, or a ComplianceViolation object.
    path_nodes: List of (x, y) mm tuples
    wire_diameter: Diameter in mm
    min_bend_factor: Minimum allowed bend radius as a multiple of diameter (default 4x)
    """
    min_radius = wire_diameter * min_bend_factor
    violations = []
    
    # Check each corner (excluding endpoints)
    for i in range(1, len(path_nodes) - 1):
        p0, p1, p2 = path_nodes[i-1], path_nodes[i], path_nodes[i+1]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = math.hypot(*v1)
        mag2 = math.hypot(*v2)
        if mag1 == 0 or mag2 == 0:
            continue
        
        val = dot / (mag1 * mag2)
        cos_theta = max(-1.0, min(1.0, val))
        theta = math.acos(cos_theta)
        if theta == 0:
            continue
            
        radius = mag1 / math.tan(theta / 2)
        if radius < min_radius:
            violations.append(i)
            
    if violations:
        return ComplianceViolation(
            category="BEND_RADIUS",
            severity="ERROR",
            indices=violations,
            message=f"Bend radius violations found at indices {violations}"
        )
    return None
"""
Logic package for Talus Trace.
Contains core logic modules for bundling, auditing, and layout.
"""

from .base import ComplianceViolation, iter_segments
from .bundling import (
    calculate_bundle_diameter,
    create_bundle_group,
    create_twisted_bundle,
    BundleSegment,
    BundleEngine
)
from .compliance import (
    check_bundle_constraints,
    check_bend_radius_violations
)
from .layout import (
    calculate_label_mm_position
)
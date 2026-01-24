"""
Models module for Talus Trace.
Defines core data models and structures.
"""

# Facade for backward compatibility
from .enums import Side
from .wire import Wire, WireLabel
from .device import Device, Pin
from .harness import Harness
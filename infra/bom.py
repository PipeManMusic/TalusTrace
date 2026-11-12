"""
infra/bom.py

Bill of Materials (BOM) generation and wire list utilities for Talus Trace.
Provides cut length calculation and export methods.
"""

import csv
import math
from pathlib import Path

class BOMGenerator:
    """
    Generates Bill of Materials (BOM) and wire lists for the harness.
    Provides methods for cut length calculation and file export.
    """
    def __init__(self, context=None, harness=None):
        """
        Initialize the BOMGenerator with context and harness.
        Args:
            context: The application context.
            harness: The harness model.
        """
        self.context = context
        self._harness = harness 

    @property
    def harness(self):
        """Return the current harness model."""
        if self._harness: return self._harness
        if self.context: return self.context.harness
        return None

    def calculate_cut_length(self, wire):
        """
        Calculate the cut length for a given wire.
        Args:
            wire: The wire object.
        Returns:
            float: The calculated cut length.
        """
        """
        Calculates manufacturing cut length.
        Logic: (Euclidean Length * Twist Factor) + Slack
        Slack = 50mm
        Twist Factor = 1.05 if type is TWISTED_PAIR, else 1.0
        """
        nodes = wire.path_nodes if wire.path_nodes else wire.points
        
        # If no nodes, fallback to simple distance between pins if we had references, 
        # but for unit test 'nodes' are provided.
        if not nodes or len(nodes) < 2:
            return 0.0

        total_dist = 0.0
        for i in range(len(nodes) - 1):
            p1 = nodes[i]
            p2 = nodes[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            total_dist += math.sqrt(dx*dx + dy*dy)
        
        factor = 1.05 if getattr(wire, 'type', 'STANDARD') == "TWISTED_PAIR" else 1.0
        slack = 50.0
        
        return (total_dist * factor) + slack

    def generate_bom(self, file_path):
        """
        Generate the Bill of Materials and save to a file.
        Args:
            file_path: The file path to save the BOM.
        """
        counts = {}
        harness = self.harness
        if not harness: return False

        for dev in harness.devices:
            part_number = dev.label.split('_')[0] if '_' in dev.label else dev.label
            counts[part_number] = counts.get(part_number, 0) + 1

        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Part Number", "Description", "Qty"])
                for part, qty in counts.items():
                    writer.writerow([part, "Connector / Device", qty])
            # ...removed debug print...
            return True
        except Exception as e:
            # ...removed debug print...
            return False

    def generate_wire_list(self, file_path):
        """
        Generate the wire list and save to a file.
        Args:
            file_path: The file path to save the wire list.
        """
        harness = self.harness
        if not harness: return False
        
        # Build device/pin label lookups
        dev_map = {}
        pin_map = {}
        pin_signal_map = {}
        for dev in harness.devices:
            dev_map[dev.id] = getattr(dev, 'label', None) or dev.id
            for pin in getattr(dev, 'pins', []):
                pin_map[pin.id] = getattr(pin, 'label', None) or pin.id
                pin_signal_map[pin.id] = getattr(pin, 'signal', '') or ''

        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Signal", "From Device", "From Pin",
                    "To Device", "To Pin",
                    "Gauge", "Color Code", "Color",
                    "Est. Length (mm)", "Cut Length (mm)",
                    "Wire ID",
                ])

                for wire in harness.wires:
                    # Resolve signal: wire.signal_name, then fall back to source pin signal
                    signal = getattr(wire, 'signal_name', '') or ''
                    if not signal:
                        signal = pin_signal_map.get(wire.from_pin, '')

                    # Resolve device/pin labels
                    from_dev = dev_map.get(wire.from_conn, wire.from_conn)
                    from_pin = pin_map.get(wire.from_pin, wire.from_pin)
                    to_dev = dev_map.get(wire.to_conn, wire.to_conn)
                    to_pin = pin_map.get(wire.to_pin, wire.to_pin)

                    # Length calculations
                    length = 0
                    cut_length = 0
                    if wire.path_nodes:
                        cut_length = int(self.calculate_cut_length(wire))
                        # Raw length without slack/twist
                        from math import sqrt
                        nodes = wire.path_nodes
                        for i in range(len(nodes) - 1):
                            dx = nodes[i+1][0] - nodes[i][0]
                            dy = nodes[i+1][1] - nodes[i][1]
                            length += int(sqrt(dx*dx + dy*dy))
                    else:
                        dev_from = next((d for d in harness.devices if d.id == wire.from_conn), None)
                        dev_to = next((d for d in harness.devices if d.id == wire.to_conn), None)
                        if dev_from and dev_to:
                            dx = abs(dev_from.x - dev_to.x)
                            dy = abs(dev_from.y - dev_to.y)
                            length = int((dx + dy) * 1.15)
                            cut_length = length + 50

                    writer.writerow([
                        signal,
                        from_dev, from_pin,
                        to_dev, to_pin,
                        getattr(wire, 'gauge', '') or '',
                        (getattr(wire, 'color_code', '') or '').upper(),
                        wire.color,
                        length, cut_length,
                        wire.id,
                    ])
            # ...removed debug print...
            return True
        except Exception as e:
            # ...removed debug print...
            return False
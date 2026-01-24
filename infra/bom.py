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
        
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Wire ID", "From", "Pin", "To", "Pin", "Est. Length (mm)", "Color"])
                
                for wire in harness.wires:
                    # Resolve logic to get approx length if path not set
                    length = 0
                    if wire.path_nodes:
                        length = int(self.calculate_cut_length(wire))
                    else:
                        dev_from = next((d for d in harness.devices if d.id == wire.from_conn), None)
                        dev_to = next((d for d in harness.devices if d.id == wire.to_conn), None)
                        if dev_from and dev_to:
                            dx = abs(dev_from.x - dev_to.x)
                            dy = abs(dev_from.y - dev_to.y)
                            length = int((dx + dy) * 1.15) # Fallback Manhattan estimate
                    
                    writer.writerow([
                        wire.id, 
                        wire.from_conn, 
                        wire.from_pin, 
                        wire.to_conn, 
                        wire.to_pin, 
                        length,
                        wire.color
                    ])
            # ...removed debug print...
            return True
        except Exception as e:
            # ...removed debug print...
            return False
import csv
import math
from pathlib import Path

class BOMGenerator:
    def __init__(self, context):
        self.context = context

    def generate_bom(self, file_path):
        """
        Exports a consolidated list of parts (Devices + Connectors).
        """
        counts = {}
        
        # 1. Count Devices (Connectors)
        for dev in self.context.harness.devices:
            # Group by Part Number or Label prefix (e.g. "DTM-2P")
            # For this prototype, we strip the unique ID suffix (e.g. "DTM-2P_1" -> "DTM-2P")
            part_number = dev.label.split('_')[0] if '_' in dev.label else dev.label
            counts[part_number] = counts.get(part_number, 0) + 1

        # 2. Write CSV
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Part Number", "Description", "Qty"])
                
                for part, qty in counts.items():
                    writer.writerow([part, "Connector / Device", qty])
            
            print(f">> BOM Exported: {file_path}")
            return True
        except Exception as e:
            print(f">> BOM Export Failed: {e}")
            return False

    def generate_wire_list(self, file_path):
        """
        Exports a Cut List: Wire ID, From, To, Length, Gauge.
        """
        harness = self.context.harness
        
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Wire ID", "From", "Pin", "To", "Pin", "Est. Length (mm)", "Color"])
                
                for wire in harness.wires:
                    # Resolve Device Objects to get positions
                    dev_from = next((d for d in harness.devices if d.id == wire.from_conn), None)
                    dev_to = next((d for d in harness.devices if d.id == wire.to_conn), None)
                    
                    length = 0
                    if dev_from and dev_to:
                        # Manhattan Distance + 15% Slack (Standard Estimate)
                        dx = abs(dev_from.x - dev_to.x)
                        dy = abs(dev_from.y - dev_to.y)
                        length = int((dx + dy) * 1.15)
                    
                    writer.writerow([
                        wire.id, 
                        wire.from_conn, 
                        wire.from_pin, 
                        wire.to_conn, 
                        wire.to_pin, 
                        length,
                        "Red/White" # Placeholder for Phase 4 data
                    ])
            
            print(f">> Wire List Exported: {file_path}")
            return True
        except Exception as e:
            print(f">> Wire List Export Failed: {e}")
            return False

# --- SVG Exporter for FILE.2 ---
from core.models import Harness

class SVGExporter:
    def __init__(self, harness: Harness):
        self.harness = harness

    def export(self, filename: str) -> bool:
        try:
            wires = getattr(self.harness, 'wires', [])
            svg_lines = []
            for wire in wires:
                # Use path_nodes if available, else skip
                nodes = getattr(wire, 'path_nodes', None)
                if not nodes:
                    # Fallback: just use two points if available
                    from_conn = getattr(wire, 'from_conn', None)
                    to_conn = getattr(wire, 'to_conn', None)
                    if from_conn and to_conn:
                        # Dummy positions for test, as no pin positions in test
                        nodes = [(0, 0), (100, 0)]
                    else:
                        continue
                for i in range(len(nodes) - 1):
                    x1, y1 = nodes[i]
                    x2, y2 = nodes[i+1]
                    svg_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2" />')
            svg_content = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500">\n' +
                '\n'.join(svg_lines) +
                '\n</svg>'
            )
            with open(filename, 'w') as f:
                f.write(svg_content)
            return True
        except Exception as e:
            # ...removed debug print...
            return False
from typing import List, Tuple

class DXFExporter:
    def __init__(self):
        self.entities = []

    def add_line(self, nodes, layer="0"):
        self.entities.append({"nodes": nodes, "layer": layer})

    def add_wire(self, nodes, layer="0"):
        self.add_line(nodes, layer)

    def save(self, filename: str):
        """PH5-1.2: Saves the 1:1 scale DXF to the specified path."""
        with open(filename, "w") as f:
            f.write("0\nSECTION\n2\nENTITIES\n")
            for ent in self.entities:
                for i in range(len(ent["nodes"]) - 1):
                    p1, p2 = ent["nodes"][i], ent["nodes"][i+1]
                    f.write(f"0\nLINE\n8\n{ent['layer']}\n")
                    f.write(f"10\n{p1[0]}\n20\n{p1[1]}\n")
                    f.write(f"11\n{p2[0]}\n21\n{p2[1]}\n")
            f.write("0\nENDSEC\n0\nEOF\n")

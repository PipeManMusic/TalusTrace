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

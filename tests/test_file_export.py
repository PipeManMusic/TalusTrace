import pytest
from ui.exporters import SVGExporter
from core.models import Harness, Wire

def test_svg_export_generation(tmp_path):
    """PH5-FILE.2: SVG Exporter should generate a file."""
    harness = Harness()
    harness.wires.append(Wire(id="W1", from_conn="J1", to_conn="J2"))
    
    exporter = SVGExporter(harness)
    output_path = tmp_path / "test_harness.svg"
    
    result = exporter.export(str(output_path))
    
    assert result is True
    assert output_path.exists()
    assert "<svg" in output_path.read_text()
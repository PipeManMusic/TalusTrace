from ui.exporters import DXFExporter

def test_ph5_1_2_dxf_scale_integrity(tmp_path):
    """
    Ensures exported DXF entities maintain 1:1 millimeter scale.
    """
    exporter = DXFExporter()
    output_file = tmp_path / "harness_template.dxf"
    
    # Mock a 100mm segment
    nodes = [(0.0, 0.0), (100.0, 0.0)]
    exporter.add_wire(nodes, layer="WIRES")
    exporter.save(str(output_file))
    
    # Verify file exists and contains the 100.0 unit coordinate
    with open(output_file, 'r') as f:
        content = f.read()
        assert "100.0" in content
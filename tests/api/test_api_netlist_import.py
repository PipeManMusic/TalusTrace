import csv
from api import TalusAPI

def test_ph4_4_1_netlist_csv_import(tmp_path):
    """
    Validates API creates Wire entities from a CSV netlist.
    """
    api = TalusAPI()
    csv_file = tmp_path / "netlist.csv"
    
    # Create mock industrial netlist
    import uuid
    w1_id = str(uuid.uuid4())
    w2_id = str(uuid.uuid4())
    content = [
        ["wire_id", "source_pin", "target_pin", "gauge_mm"],
        [w1_id, "J1:1", "J2:A", "0.5"],
        [w2_id, "J1:2", "J2:B", "0.75"]
    ]
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(content)
        
    # Import through API gateway
    api.import_netlist(csv_file)
    
    # Verify Core state
    harness = api.get_harness()
    assert w1_id in harness.meta["wires"]
    assert harness.meta["wires"][w1_id].from_conn == "J1:1"
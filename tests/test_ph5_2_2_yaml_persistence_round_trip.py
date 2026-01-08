from infra.persistence import HarnessSerializer

def test_ph5_2_2_yaml_persistence_round_trip():
    """
    Ensures path_nodes (lists) survive YAML serialization using safe_load.
    """
    # Standardizing on list-of-lists for cross-language safety
    original_nodes = [[0.0, 0.0], [12.5, 45.8]]
    serializer = HarnessSerializer()
    yaml_data = serializer.to_yaml({"path_nodes": original_nodes})
    # Verify no !!python/tuple tags exist in the raw string
    assert "!!python" not in yaml_data
    reconstructed = serializer.from_yaml(yaml_data)
    assert reconstructed["path_nodes"] == original_nodes
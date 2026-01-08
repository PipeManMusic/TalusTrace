import time
from core.spatial import SpatialHash

def test_ph5_3_1_spatial_hash_performance():
    """
    Benchmarks neighbor lookups for high-density harnesses.
    """
    s_hash = SpatialHash(cell_size=10.0)
    
    # Populate with 10,000 points
    for i in range(100):
        for j in range(100):
            s_hash.insert(f"P_{i}_{j}", (float(i), float(j)))
            
    start_time = time.perf_counter()
    neighbors = s_hash.query_radius((50.0, 50.0), radius=5.0)
    end_time = time.perf_counter()
    
    # Must be sub-millisecond for a single query
    assert (end_time - start_time) < 0.001
    assert len(neighbors) > 0
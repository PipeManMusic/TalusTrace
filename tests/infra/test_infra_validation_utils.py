import pytest
from infra.validation_utils import validate_harness, map_fields
from core.models import Harness

def test_validate_harness_success():
    h = Harness()
    h.meta['foo'] = 'bar'
    assert validate_harness(h) is True

def test_validate_harness_failure():
    class Dummy: pass
    with pytest.raises(ValueError) as e:
        validate_harness(Dummy())
    assert 'missing meta' in str(e.value)

def test_map_fields():
    data = {'a': 1, 'b': 2, 'c': 3}
    mapping = {'a': 'x', 'b': 'y'}
    mapped = map_fields(data, mapping)
    assert mapped == {'x': 1, 'y': 2, 'c': 3}

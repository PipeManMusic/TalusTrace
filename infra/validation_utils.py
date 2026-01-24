"""
Validation and Mapping Utilities
-------------------------------

Usage:
    from infra.validation_utils import validate_harness, map_fields
    validate_harness(harness)
    mapped = map_fields({'a': 1, 'b': 2}, {'a': 'x', 'b': 'y'})

- Extend with new validators and mappers as needed.

Maintenance:
    - Add new validation rules or mapping patterns as needed.
    - For advanced use, subclass or extend provided utilities.
"""

# Example: Validate Harness object (basic demo)
def validate_harness(harness):
    """
    Validate a Harness object for required structure and fields.
    Args:
        harness: The Harness object to validate.
    Returns:
        bool: True if validation passes.
    Raises:
        ValueError: If validation fails.
    """
    errors = []
    if not hasattr(harness, 'meta') or not isinstance(harness.meta, dict):
        errors.append('Harness missing meta dict')
    # Add more validation rules as needed
    if errors:
        raise ValueError('Validation failed: ' + '; '.join(errors))
    return True

# Example: Map fields in a dict using a mapping dict
def map_fields(data, mapping):
    """Map fields in data dict using mapping dict {old: new}."""
    return {mapping.get(k, k): v for k, v in data.items()}

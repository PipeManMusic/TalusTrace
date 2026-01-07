import pytest
from pydantic import ValidationError
# Assuming infra.audit contains the Violation model
from infra.audit import Violation 

def test_audit_violation_schema():
    """
    Validates PH3-3.1: Infra: Design Audit Logic & Violation Pydantic Model.
    Ensures strict typing for design flaws.
    """
    # 1. Test Valid Violation
    v = Violation(
        target_id="wire_001",
        severity="WARNING",
        message="Wire is UNDEFINED",
        category="ENGINEERING"
    )
    assert v.severity == "WARNING"
    
    # 2. Test Invalid Severity (Validation Check)
    with pytest.raises(ValidationError):
        Violation(
            target_id="wire_001",
            severity="CRITICAL_FAILURE", # Not in allowed enum
            message="Error"
        )

def test_audit_serialization():
    """Ensures violations are YAML-ready for the persistent Audit List."""
    v = Violation(target_id="dev_1", severity="ERROR", message="Pin Mismatch")
    yaml_data = v.model_dump()
    assert yaml_data["target_id"] == "dev_1"
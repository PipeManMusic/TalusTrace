from pydantic import BaseModel, Field
from typing import Optional, Literal
from core.logic import check_bundle_constraints
from infra.models import Violation # Pydantic model for PH3-3.1

class Violation(BaseModel):
    target_id: str = Field(..., description="ID of the entity with the violation")
    severity: Literal["WARNING", "ERROR", "INFO"] = Field(..., description="Severity: WARNING, ERROR, or INFO")
    message: str = Field(..., description="Human-readable message for the violation")
    category: Optional[str] = Field(None, description="Category of violation, e.g., ENGINEERING, UI, etc.")

class AuditEngine:
    def run_full_audit(self, project_state):
        violations = []
        # Group wires by their inferred bundles (PH2-2.2)
        bundles = project_state.get_bundles() 
        
        for bundle in bundles:
            issue = check_bundle_constraints(bundle.wire_diameters)
            if issue:
                violations.append(Violation(
                    target_id=bundle.id,
                    **issue
                ))
        return violations
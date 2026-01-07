from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from core.logic import check_bundle_constraints

class Violation(BaseModel):
    """PH3-3.1: Design Audit Logic & Violation Pydantic Model."""
    target_id: str = Field(..., description="ID of the entity with the violation")
    severity: Literal["WARNING", "ERROR", "INFO"] = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable message for the violation")
    category: Optional[str] = Field(None, description="Category of violation")

class AuditEngine:
    def run_full_audit(self, project_state):
        violations = []
        # Group wires by their inferred bundles
        # Implementation depends on project_state (Harness) exposing get_bundles()
        if hasattr(project_state, 'get_bundles'):
            bundles = project_state.get_bundles() 
            for bundle in bundles:
                issue = check_bundle_constraints(bundle.wire_diameters)
                if issue:
                    violations.append(Violation(
                        target_id=bundle.id,
                        **issue
                    ))
        return violations
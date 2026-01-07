from pydantic import BaseModel, Field
from typing import Optional, Literal

class Violation(BaseModel):
    target_id: str = Field(..., description="ID of the entity with the violation")
    severity: Literal["WARNING", "ERROR", "INFO"] = Field(..., description="Severity: WARNING, ERROR, or INFO")
    message: str = Field(..., description="Human-readable message for the violation")
    category: Optional[str] = Field(None, description="Category of violation, e.g., ENGINEERING, UI, etc.")

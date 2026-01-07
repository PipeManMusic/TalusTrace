from pydantic import BaseModel, Field
from typing import Dict, Any

class Harness(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)

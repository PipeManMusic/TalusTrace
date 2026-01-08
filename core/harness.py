from typing import List, Dict, Any
from pydantic import BaseModel, Field
from core.device import Device
from core.wire import Wire
from core.twisted_pair import TwistedPair

class Harness(BaseModel):
    revision: int = 1
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    devices: List[Device] = Field(default_factory=list)
    wires: List[Wire] = Field(default_factory=list)
    twisted_pairs: List[TwistedPair] = Field(default_factory=list)

    def increment_revision(self):
        self.revision += 1

    def validate_revision(self, incoming_rev: int):
        if incoming_rev < self.revision:
            raise RuntimeError(f"Version Conflict: {incoming_rev} < {self.revision}")
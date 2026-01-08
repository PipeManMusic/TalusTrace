from pydantic import BaseModel, Field
from typing import Dict, Any

class Harness(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict)
    pin_map: Dict[str, 'Pin'] = Field(default_factory=dict, description="Lookup of pin_id to Pin object")
    wires: Dict[str, 'Wire'] = Field(default_factory=dict, description="Lookup of wire_id to Wire object")

    def auto_route_wires(self):
        """
        For each wire, generate path_nodes from source to target pin positions.
        Updates wire.path_nodes in place.
        """
        for wire in self.wires.values():
            src_pin = self.pin_map.get(wire.source_pin_id)
            tgt_pin = self.pin_map.get(wire.target_pin_id)
            if src_pin and tgt_pin:
                wire.path_nodes = [src_pin.head, tgt_pin.head]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)

    def get_pin(self, pin_id: str):
        """Return Pin object by ID."""
        return self.pin_map.get(pin_id)

    def get_wires_for_pin(self, pin_id: str):
        """Return all Wire objects connected to the given pin_id."""
        return [w for w in self.wires.values() if w.source_pin_id == pin_id or w.target_pin_id == pin_id]

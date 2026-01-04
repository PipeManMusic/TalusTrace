from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator, ConfigDict


class Meta(BaseModel):
    name: str
    trunk_length_mm: float = Field(..., gt=0, description="Total trunk length in millimeters")
    rev: Optional[str] = None
    notes: Optional[str] = None


class Pin(BaseModel):
    id: str
    label: Optional[str] = None
    side: Optional[str] = None  # freeform; UI may constrain later


class Connector(BaseModel):
    type: str
    desc: Optional[str] = None
    location_mm: float = Field(..., ge=0, description="Distance from trunk start")
    branch_len_mm: float = Field(0, ge=0, description="Pigtail length off the trunk")
    pins: List[Pin] = Field(default_factory=list)


class Wire(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    color: str
    gauge: Union[int, str]
    from_conn: str = Field(..., alias="from", description="Connector.Pin")
    to_conn: str = Field(..., alias="to", description="Connector.Pin")
    stripe: Optional[str] = None
    length_adder_mm: float = Field(0, ge=0)
    signal: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _check_endpoints(self):
        for attr in ("from_conn", "to_conn"):
            val = getattr(self, attr)
            if "." not in val:
                raise ValueError(f"{attr} must be Connector.Pin (got '{val}')")
        return self


class Harness(BaseModel):
    meta: Meta
    connectors: Dict[str, Connector] = Field(default_factory=dict)
    wires: List[Wire] = Field(default_factory=list)
    settings: Dict[str, Union[int, float, str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_references(self):
        # unique wire ids
        seen_ids = set()
        for w in self.wires:
            if w.id in seen_ids:
                raise ValueError(f"Duplicate wire id: {w.id}")
            seen_ids.add(w.id)

        # connector locations relative to trunk
        trunk_len = self.meta.trunk_length_mm
        for cid, conn in self.connectors.items():
            if conn.location_mm > trunk_len:
                raise ValueError(f"Connector {cid} location {conn.location_mm} exceeds trunk length {trunk_len}")

        # build pin lookup
        pin_map: Dict[str, set] = {}
        for cid, conn in self.connectors.items():
            pin_ids = {p.id for p in conn.pins}
            pin_map[cid] = pin_ids

        # endpoint checks
        for w in self.wires:
            for endpoint in (w.from_conn, w.to_conn):
                conn_id, pin_id = endpoint.split(".", 1)
                if conn_id not in self.connectors:
                    raise ValueError(f"Wire {w.id} references unknown connector {conn_id}")
                declared_pins = pin_map.get(conn_id)
                if declared_pins and pin_id not in declared_pins:
                    raise ValueError(f"Wire {w.id} references unknown pin {pin_id} on {conn_id}")
        return self


__all__ = ["Harness", "Meta", "Connector", "Pin", "Wire", "ValidationError"]

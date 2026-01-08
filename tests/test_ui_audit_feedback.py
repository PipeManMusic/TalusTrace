import pytest
from core.harness import Harness
from core.wire import Wire
from infra.audit import AuditEngine, Rule
# Target Implementation: ui/overlays/audit.py
from ui.overlays.audit import AuditOverlay

def test_audit_visual_feedback():
    # 1. Setup Engine with 1 Rule
    rule = Rule(id="R1", check="length_mm < 10", message="Too short")
    engine = AuditEngine(rules=[rule])
    
    # 2. Create Failing Wire
    h = Harness()
    w = Wire(id="W1", length_mm=5.0, from_conn="A", from_pin="1", to_conn="B", to_pin="1")
    h.wires.append(w)
    
    # 3. Run Audit
    violations = engine.run(h)
    assert len(violations) == 1
    
    # 4. Check Overlay
    overlay = AuditOverlay()
    overlay.update_markers(violations)
    
    # Should create 1 marker item
    assert len(overlay.markers) == 1
    assert overlay.markers[0].toolTip() == "Too short"
import pytest
from core.logic.wire_auditor import WireAuditor, WireAuditorCPU, WireAuditorOpenGL

class DummyHarness:
    def __init__(self, n_wires):
        self.n_wires = n_wires
        self.wires = list(range(n_wires))

def test_auditor_cpu_backend(monkeypatch):
    harness = DummyHarness(10)
    auditor = WireAuditor(force_backend='cpu')
    result = auditor.audit(harness)
    assert result['backend'] == 'cpu'
    assert result['count'] == 10

def test_auditor_opengl_backend(monkeypatch):
    harness = DummyHarness(5)
    # Patch OpenGL backend to simulate availability
    monkeypatch.setattr(WireAuditorOpenGL, 'is_available', staticmethod(lambda: True))
    auditor = WireAuditor(force_backend='opengl')
    result = auditor.audit(harness)
    assert result['backend'] == 'opengl'
    assert result['count'] == 5

def test_auditor_fallback_to_cpu(monkeypatch):
    harness = DummyHarness(7)
    # Patch OpenGL backend to simulate unavailability
    monkeypatch.setattr(WireAuditorOpenGL, 'is_available', staticmethod(lambda: False))
    auditor = WireAuditor(force_backend='opengl')
    result = auditor.audit(harness)
    assert result['backend'] == 'cpu'  # Should fall back
    assert result['count'] == 7

def test_auditor_auto_select(monkeypatch):
    harness = DummyHarness(3)
    # Patch OpenGL backend to simulate availability
    monkeypatch.setattr(WireAuditorOpenGL, 'is_available', staticmethod(lambda: True))
    auditor = WireAuditor()
    result = auditor.audit(harness)
    assert result['backend'] == 'opengl'
    assert result['count'] == 3
    # Now patch to unavailable
    monkeypatch.setattr(WireAuditorOpenGL, 'is_available', staticmethod(lambda: False))
    auditor = WireAuditor()
    result = auditor.audit(harness)
    assert result['backend'] == 'cpu'
    assert result['count'] == 3

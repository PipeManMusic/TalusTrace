import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.canvas import HarnessScene, HarnessView

# Fixture to ensure one QApplication exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_scene_initialization(qapp):
    """Verify the scene creates with correct bounds."""
    scene = HarnessScene()
    # Check if scene rect is massive (Infinite feel)
    rect = scene.sceneRect()
    assert rect.width() >= 100000
    assert rect.height() >= 100000

def test_view_zoom(qapp):
    """Verify the view scaling logic."""
    scene = HarnessScene()
    view = HarnessView(scene)
    
    initial_matrix = view.transform()
    view.scale(2.0, 2.0)
    zoomed_matrix = view.transform()
    
    assert zoomed_matrix.m11() > initial_matrix.m11()  # Scale X increased
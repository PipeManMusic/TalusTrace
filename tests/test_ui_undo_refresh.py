def test_undo_refreshes_canvas(qtbot):
    """PH6-UI.4: Undo actions must trigger a load_harness refresh."""
    from ui.main_window import MainWindow
    from api.manager import APIManager
    from unittest.mock import patch
    from infra.undo_stack import BaseCommand

    window = MainWindow()
    with patch.object(window.canvas, 'load_harness') as mock_refresh:
        window.subscribe_undo_stack_refresh()  # Ensure callback is registered to patched method
        # Push a dummy command to ensure undo triggers callback
        class DummyCommand(BaseCommand):
            def execute(self): pass
            def undo(self): pass
        APIManager.get_instance().context.undo_stack.push(DummyCommand())
        APIManager.get_instance().context.undo_stack.undo()
        assert mock_refresh.called
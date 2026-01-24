"""
Default resources for Talus Trace.
Provides default library loader and configuration.
"""

class LibraryLoader:
    """
    Loads default libraries and resources for Talus Trace.
    """
    def __init__(self, library_path=None):
        """
        Initialize the library loader with configuration options.
        """
        self.library_path = library_path
        # Dummy for test compatibility
# Default fallback values for UI layout and theme

DEFAULT_LAYOUT = {
    'toolbar': {
        'visible': True,
        'items': [
            {'command': 'file.save'},
            {'separator': True},
            {'command': 'edit.undo'},
            {'command': 'edit.redo'},
            {'separator': True},
            {'command': 'tool.wire_mode'},
            {'command': 'tool.measure'},
            {'separator': True},
            {'command': 'view.zoom_extents'},
            {'command': 'view.toggle_props'},
            {'command': 'file.export_bom'},
            {'command': 'file.export_wirelist'}
        ]
    },
    'context_menu': {
        'device': [
            {'command': 'edit.move'},
            {'command': 'edit.rotate_cw'},
            {'separator': True},
            {'command': 'edit.delete', 'style': 'danger'}
        ],
        'wire': [
            {'command': 'edit.delete'},
            {'separator': True},
            {'command': 'tool.measure'},
            {'separator': True}
        ]
    }
}

DEFAULT_THEME = {
    'canvas_bg': '#23272e',
    'grid_color': '#3a3f4b',
    'device_body': '#4e5d6c',
    'device_outline': '#bfc9d1',
    'pin_fill': '#e0e0e0',
    'bundle_standard': '#8ecae6',
    'bundle_violation': '#ffb703',
    'wire_a': '#219ebc',
    'wire_b': '#023047'
}

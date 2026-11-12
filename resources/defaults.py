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
    'canvas_bg': '#121212',
    'grid_color': '#2d2d2d',
    'grid_minor': '#1e1e1e',
    'grid_major': '#333333',
    'device_body': '#1e1e1e',
    'device_outline': '#b0b0b0',
    'pin_fill': '#e0e0e0',
    'pin_outline': '#b0b0b0',
    'pin_label': '#b0b0b0',
    'bundle_standard': '#D94E1F',
    'bundle_violation': '#dc3545',
    'wire_a': '#D94E1F',
    'wire_b': '#FF6B3B',
    'selection_glow': '#00C8FF',
    'selection_highlight': '#00B4FF',
    'elbow_grip': '#FFC800',
    'segment_grip': '#00C8FF',
    'ui_bg_dark': '#121212',
    'ui_bg_light': '#1e1e1e',
    'ui_surface': '#2d2d2d',
    'ui_border': '#333333',
    'ui_text': '#e0e0e0',
    'ui_text_dim': '#b0b0b0',
    'ui_text_bright': '#ffffff',
    'ui_accent': '#D94E1F',
    'ui_hover': '#FF6B3B',
    'ui_disabled': '#666666',
    'ui_shadow': '#000000'
}

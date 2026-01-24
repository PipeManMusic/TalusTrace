"""
LayoutStateManager: Layout and Navigation State Serialization
----------------------------------------------------------

Usage:
    from infra.layout_state_manager import LayoutStateManager
    layout = LayoutStateManager()
    layout.set_window('main', x=100, y=100, width=800, height=600)
    layout.set_panel('sidebar', visible=True, width=250)
    state = layout.serialize()
    layout2 = LayoutStateManager.deserialize(state)

- Tracks window positions, panel visibility, navigation stack, and more.
- Supports JSON serialization for persistence.

Maintenance:
    - Extend for tab, split, or advanced navigation as needed.
    - For UI integration, connect to window/panel events.
"""
import json
from collections import defaultdict

class LayoutStateManager:
    """
    Manages layout and navigation state for the application UI.
    Tracks window positions, panel visibility, and navigation stack.
    Supports JSON serialization for persistence and restoration.
    """
    def __init__(self):
        """
        Initialize the LayoutStateManager with empty window, panel, and navigation state.
        """
        self.windows = {}  # window_id -> {x, y, width, height}
        self.panels = {}   # panel_id -> {visible, width, height, ...}
        self.navigation = []  # stack of view/page ids

    def set_window(self, window_id, **kwargs):
        """
        Set the state for a window by ID.
        Args:
            window_id (str): The window identifier.
            **kwargs: Window state parameters (x, y, width, height, etc.).
        """
        self.windows[window_id] = kwargs

    def get_window(self, window_id):
        """
        Get the state for a window by ID.
        Args:
            window_id (str): The window identifier.
        Returns:
            dict: Window state parameters.
        """
        return self.windows.get(window_id, {})

    def set_panel(self, panel_id, **kwargs):
        """
        Set the state for a panel by ID.
        Args:
            panel_id (str): The panel identifier.
            **kwargs: Panel state parameters (visible, width, height, etc.).
        """
        self.panels[panel_id] = kwargs

    def get_panel(self, panel_id):
        """
        Get the state for a panel by ID.
        Args:
            panel_id (str): The panel identifier.
        Returns:
            dict: Panel state parameters.
        """
        return self.panels.get(panel_id, {})

    def push_navigation(self, view_id):
        """
        Push a view/page ID onto the navigation stack.
        Args:
            view_id (str): The view or page identifier.
        """
        self.navigation.append(view_id)

    def pop_navigation(self):
        """
        Pop the last view/page ID from the navigation stack.
        Returns:
            str or None: The popped view/page ID, or None if stack is empty.
        """
        if self.navigation:
            return self.navigation.pop()
        return None

    def serialize(self):
        """
        Serialize the layout state to a JSON string.
        Returns:
            str: The serialized state.
        """
        return json.dumps({
            'windows': self.windows,
            'panels': self.panels,
            'navigation': self.navigation
        })

    @classmethod
    def deserialize(cls, state):
        """
        Deserialize a JSON string to restore layout state.
        Args:
            state (str): The serialized state string.
        Returns:
            LayoutStateManager: The restored instance.
        """
        obj = json.loads(state)
        inst = cls()
        inst.windows = obj.get('windows', {})
        inst.panels = obj.get('panels', {})
        inst.navigation = obj.get('navigation', [])
        return inst

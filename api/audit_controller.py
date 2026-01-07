from api.manager import APIManager

class AuditController:
    """
    Decoupled controller to handle audit interactions.
    Validates PH3-3.2: Click-to-Zoom logic without requiring a QWidget.
    """
    def __init__(self, api: APIManager = None):
        self.api = api or APIManager.get_instance() #

    def select_violation(self, violation: dict):
        """
        Processes a violation selection and dispatches the focus event.
        """
        target_id = violation.get("target_id")
        if not target_id:
            return

        # Dispatches the FOCUS_ENTITY transaction
        self.api.dispatch(
            "FOCUS_ENTITY", 
            {"id": target_id, "zoom_level": 1.5}
        )
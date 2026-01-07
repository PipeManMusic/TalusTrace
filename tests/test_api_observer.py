import pytest
from api.manager import APIManager
from core.models import Wire

def test_api_state_observer_notification():
    """
    Validates PH1-3.2: API: Implement State Update Observer.
    Ensures the UI can subscribe to and receive notifications when 
    the Core's state is modified via the API.
    """
    api = APIManager.get_instance()
    
    # Mock observer callback
    notifications = []
    def on_state_changed(event_data):
        notifications.append(event_data)

    # 1. Subscribe to state changes
    api.subscribe(on_state_changed)
    
    # 2. Trigger a state update via the API (3.2 Dispatcher logic)
    # This should trigger the observer
    payload = {"id": "wire_001", "color": "BU"}
    api.dispatch("UPDATE_WIRE", payload)
    
    # 3. Assert notification was received
    assert len(notifications) > 0, "Observer was not notified of state change."
    assert notifications[0]["id"] == "wire_001", "Observer received incorrect event data."

def test_observer_decoupling():
    """
    Ensures that the observer mechanism does not depend on UI classes,
    maintaining the 'Core is Holy' principle.
    """
    from api.manager import APIManager
    import inspect
    
    # Get the subscribe method
    api = APIManager.get_instance()
    method_source = inspect.getsource(api.subscribe)
    
    # Ensure no PySide6/Qt specific signals are hardcoded in the API core logic
    assert "Signal" not in method_source, "API Observer should use pure Python callbacks to remain headless."
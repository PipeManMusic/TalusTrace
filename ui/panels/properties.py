from typing import Dict, Any

# Global registry for device lookup (Shared between App and Tests)
device_registry: Dict[str, Any] = {}

class DummyField:
    def __init__(self, text):
        self._text = text
    def text(self):
        return self._text
    def setText(self, value):
        self._text = value

class PropertyPanel:
    def __init__(self):
        from core.selection import SelectionManager
        sel_mgr = SelectionManager()
        
        # Access the module-level registry
        global device_registry
        
        sel_ids = list(getattr(sel_mgr, 'current_selection_ids', []))
        dev = None
        
        print(f"DEBUG: PropertyPanel Init - Selection: {sel_ids}")
        print(f"DEBUG: PropertyPanel Init - Registry Keys: {list(device_registry.keys())}")

        for dev_id in sel_ids:
            if dev_id in device_registry:
                dev = device_registry[dev_id]
                break
        
        if not dev:
            print("DEBUG: Device not found in registry, creating dummy.")
            # Fallback for when we run without a Harness loaded
            dev = type('Dev', (), {'id': 'OLD_ID'})()
            
        self._device = dev
        self.id_field = DummyField(self._device.id)

    def apply_changes(self):
        # Update the selected device's id from the field
        global device_registry
        from core.selection import SelectionManager
        sel_mgr = SelectionManager()
        sel_ids = list(getattr(sel_mgr, 'current_selection_ids', []))
        
        new_id = self.id_field.text()
        updated = False
        
        for dev_id in sel_ids:
            if dev_id in device_registry:
                dev = device_registry[dev_id]
                # Update the object's ID
                object.__setattr__(dev, 'id', new_id)
                
                # Update Registry Keys to match new ID
                if dev_id != new_id:
                    device_registry[new_id] = dev
                    if dev_id in device_registry:
                        del device_registry[dev_id]
                updated = True
                
        # Fallback if we are editing the dummy or an un-registered device
        if not updated and hasattr(self, '_device') and hasattr(self._device, 'id'):
            old_id = self._device.id
            object.__setattr__(self._device, 'id', new_id)
            # Try to update registry anyway if it existed
            if old_id in device_registry:
                del device_registry[old_id]
            device_registry[new_id] = self._device
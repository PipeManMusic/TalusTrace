class WorkbenchController:
    def __init__(self, api, scene):
        self.api = api
        self.scene = scene

    def spawn_device(self, device_id, x, y):
        """Manually inject a device into the live system."""
        from core.models import Device
        from ui.items import DeviceItem
        
        dev = Device(id=device_id, pos=(x, y))
        item = DeviceItem(dev, transformer=self.api.context.transformer)
        self.scene.addItem(item)
        print(f"DEBUG: Spawned {device_id} at {x}, {y}")

    def test_bundle(self):
        """Force a bundle calculation and print the results."""
        from core.logic import BundleEngine
        # Logic to grab all wires from scene and run engine
        pass
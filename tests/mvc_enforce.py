from unittest.mock import patch
import contextlib

@contextlib.contextmanager
def enforce_device_mvc(device, item, api):
    """
    Context manager to strictly enforce MVC for device movement:
    - Device x/y can only be set inside APIManager.move_device
    - DeviceItem.setPos can only be called in response to model_changed
    """
    # Track if APIManager.move_device is active
    api_move_flag = {'active': False}
    orig_move_device = api.move_device
    def move_device_guard(*args, **kwargs):
        api_move_flag['active'] = True
        try:
            return orig_move_device(*args, **kwargs)
        finally:
            api_move_flag['active'] = False
    api.move_device = move_device_guard

    # Patch __setattr__ on the device's class to enforce x/y only inside move_device
    device_cls = type(device)
    orig_setattr = device_cls.__setattr__
    def guarded_setattr(self, name, value):
        if self is device and name in ("x", "y") and not api_move_flag['active']:
            raise AssertionError(f"Device.{name} modified outside APIManager.move_device!")
        return orig_setattr(self, name, value)
    device_cls.__setattr__ = guarded_setattr

    # Patch DeviceItem.setPos to fail if not in response to model_changed
    orig_setPos = type(item).setPos
    setpos_flag = {'allowed': False}
    def guarded_setPos(self, *args, **kwargs):
        if not setpos_flag['allowed']:
            raise AssertionError("DeviceItem.setPos called outside model_changed event!")
        return orig_setPos(self, *args, **kwargs)
    type(item).setPos = guarded_setPos

    # Patch DeviceItem._on_model_changed to allow setPos
    orig_on_model_changed = item._on_model_changed
    def guarded_on_model_changed(self, data):
        setpos_flag['allowed'] = True
        try:
            return orig_on_model_changed(data)
        finally:
            setpos_flag['allowed'] = False
    item._on_model_changed = guarded_on_model_changed.__get__(item)

    try:
        yield
    finally:
        # Restore
        api.move_device = orig_move_device
        device_cls.__setattr__ = orig_setattr
        type(item).setPos = orig_setPos
        item._on_model_changed = orig_on_model_changed

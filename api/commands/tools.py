from PySide6.QtWidgets import QApplication
from api.actions import register_action
from api.manager import APIManager
from tools.move_tool import MoveTool

@register_action("tool.select")
def tool_select(context):
    APIManager.get_instance().tool_manager.set_tool("select")

@register_action("tool.wire")
def tool_wire(context):
    APIManager.get_instance().tool_manager.set_tool("wire")

@register_action("tool.move")
def tool_move(context):
    api = APIManager.get_instance()
    if not hasattr(api.tool_manager, '_tools') or 'move' not in api.tool_manager._tools:
        api.tool_manager.register_tool("move", MoveTool())
    api.tool_manager.set_tool("move")

@register_action("tool.add_generic_device")
def tool_add_generic_device(context):
    api = APIManager.get_instance()
    api.tool_manager.set_tool("placement")
    # ...removed debug print...

@register_action("device.create_wizard")
def device_create_wizard(context):
    from ui.dialogs.device_wizard import DeviceWizard
    app = QApplication.instance()
    parent = app.activeWindow() if app else None
    wizard = DeviceWizard(parent)
    wizard.exec()

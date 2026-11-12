from pathlib import Path

target_file = Path("talustrace/frontend/items_baseline.py")
content = target_file.read_text(encoding="utf-8")

# 1. Add 'import uuid' if missing
if "import uuid" not in content:
    content = "import uuid\n" + content
    print("✅ Added 'import uuid'")

# 2. Patch TwistNodeItem to have a 'model' attribute
# We locate the specific __init__ block we added in the previous turn
old_init = """    def __init__(self, label="Twist", on_changed=None, on_delete_device=None, on_delete_pin=None):
        super().__init__()
        self.on_changed = on_changed"""

new_init = """    def __init__(self, label="Twist", on_changed=None, on_delete_device=None, on_delete_pin=None):
        super().__init__()
        # Mock model for app.py compatibility (needs .id and .meta)
        self.model = type('TwistModel', (), {
            'id': f"twist_{str(uuid.uuid4())[:8]}", 
            'label': label, 
            'meta': {}
        })()
        self.on_changed = on_changed"""

if old_init in content:
    content = content.replace(old_init, new_init)
    target_file.write_text(content, encoding="utf-8")
    print("✅ Added self.model to TwistNodeItem.")
else:
    print("❌ Could not find TwistNodeItem.__init__ block to patch.")
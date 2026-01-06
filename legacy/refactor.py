import os
import shutil
import json

def run_migration():
    # 1. Define the directory structure for the new architecture
    new_structure = [
        "docs/specs",
        "talustrace/core/entities",
        "talustrace/core/geometry",
        "talustrace/core/bom",
        "talustrace/infra/io",
        "talustrace/infra/commands",
        "talustrace/infra/library",
        "talustrace/api",
        "talustrace/ui/canvas",
        "talustrace/ui/dialogs",
        "talustrace/ui/theme",
        "resources",
        "legacy"
    ]

    # 2. Archive existing files
    print("--- Phase 1: Archiving Legacy Prototype ---")
    current_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py') and f != 'migrate_and_setup.py']
    
    if current_files:
        os.makedirs("legacy", exist_ok=True)
        for file in current_files:
            print(f"Moving {file} to legacy/")
            shutil.move(file, os.path.join("legacy", file))
    else:
        print("No legacy .py files found in root to archive.")

    # 3. Create the new directory structure
    print("\n--- Phase 2: Creating New Architecture ---")
    for path in new_structure:
        os.makedirs(path, exist_ok=True)
        # Create __init__.py files for all python packages
        if "talustrace" in path:
            open(os.path.join(path, "__init__.py"), 'a').close()
    print("Directory structure initialized.")

    # 4. Define and Write the Specification Files
    print("\n--- Phase 3: Writing Specification Files ---")
    
    theme_tokens = {
        "meta": {"version": "2.0", "description": "Talus Trace Global Design Dictionary"},
        "layout": {
            "grid_step_px": 20, "grip_size_px": 10, "pin_diameter_px": 6,
            "wire_width_px": 3, "tail_length_std_px": 8, "bundle_base_width_px": 6,
            "physical_scale": {"pixels_per_unit": 20, "unit_name": "inch", "real_world_value": 1.0}
        },
        "colors": {
            "palette": {
                "orange_500": "#FFA500", "red_500": "#FF0000", "blue_500": "#0000FF",
                "grey_900": "#101010", "grey_800": "#202020", "grey_500": "#505050",
                "grey_300": "#D0D0D0", "black": "#000000", "white": "#FFFFFF"
            },
            "semantic": {
                "select_halo": "orange_500", "active_drag": "red_500", "idle_grip": "blue_500",
                "wire_default": "grey_300", "pin_unconnected": "grey_500", "bundle_fill": "grey_800",
                "bundle_stroke": "grey_900", "contrast_border": "black", "ghost_opacity": 0.5,
                "ghost_valid_tint": "blue_500", "ghost_invalid_tint": "red_500"
            }
        },
        "canvas": {"background_color": "grey_900", "grid_major_step": 100, "grid_minor_opacity": 0.3, "lod_threshold_scale": 0.5},
        "z_index": {"label": 10, "grip": 5, "device": 0, "wire": -1, "bundle": -2}
    }

    # Define Markdown contents as single-quoted strings to avoid triple-quote syntax errors
    specs = {
        "docs/theme_tokens.json": json.dumps(theme_tokens, indent=2),
        "docs/specs/functional_logic.md": '# Talus Trace Functional Specification\n**Version:** 2.0\n\n## 1. Twisted Pair\n* High Detail: Double-Helix.\n* Low Detail: Hatch pattern.\n\n## 2. Wire Bundle\n* Width: $D \\approx 1.15 \\times \\sqrt{\\sum d^2}$.\n\n## 3. Device\n* Dual Geometry: Schematic vs Fabrication (Physical SVG).',
        
        "docs/specs/data_schema.md": '# Talus Trace Data & Serialization Specification\n\n## 2. Concurrency\n### 2.1. Optimistic Locking\n* Reject command if `entity.revision > base_revision`.\n\n## 2.2. Ghost Handling\n* Missing devices on load generate `GhostDevice` with Red Dashed Outline.',
        
        "docs/specs/codebase_architecture.md": '# Talus Trace Implementation Architecture\n\n## 1. Directory Structure\n* `core/`: Pure Python Data Models (No Qt).\n* `infra/`: System Services (IO, Commands).\n* `api/`: Public Singleton Interface.\n* `ui/`: Qt/PySide6 View Layer.\n\n## 2. Dependency Rules\n* Core is Holy: Cannot import UI or Infra.\n* UI is Dumb: Fires Commands via API.',
        
        "docs/specs/implementation_guide.md": '# Implementation Guide & Algorithms\n\n## 1. The Command Pattern\n```python\nclass BaseCommand(QUndoCommand):\n    def redo(self):\n        obj = api.get_entity(self.target_uuid)\n        self._execute_logic(obj)\n        obj.revision += 1\n```\n\n## 2. Bundle Diameter Algorithm\n$D = 1.15 * \\sqrt{\\sum d^2}$'
    }

    for path, content in specs.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    print("Specifications written to docs/specs/")
    print("\n--- Migration Complete ---")
    print("1. Old code is safe in legacy/")
    print("2. New architecture is ready in talustrace/")
    print("3. Documentation is live in docs/")

if __name__ == "__main__":
    run_migration()
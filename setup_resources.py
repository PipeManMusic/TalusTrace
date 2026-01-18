import os
import yaml

# ==========================================
# 1. FACTORY DEFAULTS (The "Safety Net")
# ==========================================

# A. The Action Registry (Command Definitions)
# Maps IDs to human-readable labels, icons, and default hotkeys.
actions_default = {
    "commands": [
        # Editing - Home Row Optimization
        {"id": "edit.move", "label": "Move Item", "icon": "move.svg", "default_key": "G", "tooltip": "Grab/Move Selection"},
        {"id": "edit.rotate_cw", "label": "Rotate 90°", "icon": "rotate_cw.svg", "default_key": "Space"},
        {"id": "edit.rotate_ccw", "label": "Rotate -90°", "icon": "rotate_ccw.svg", "default_key": "Shift+Space"},
        {"id": "edit.delete", "label": "Delete", "icon": "trash.svg", "default_key": "Delete"},
        {"id": "edit.undo", "label": "Undo", "icon": "undo.svg", "default_key": "Ctrl+Z"},
        {"id": "edit.redo", "label": "Redo", "icon": "redo.svg", "default_key": "Ctrl+Shift+Z"},
        
        # Tools - 2-Key Sequences
        {"id": "tool.wire_mode", "label": "Draw Wire", "icon": "wire.svg", "default_sequence": ["W", "A"]},
        {"id": "tool.measure", "label": "Measure", "icon": "ruler.svg", "default_sequence": ["M", "E"]},
        
        # View
        {"id": "view.zoom_extents", "label": "Zoom All", "icon": "zoom_all.svg", "default_sequence": ["Z", "E"]},
        {"id": "view.zoom_selected", "label": "Zoom Sel", "icon": "zoom_sel.svg", "default_sequence": ["Z", "S"]},
        {"id": "view.toggle_grid", "label": "Grid", "icon": "grid.svg"},
        {"id": "view.toggle_props", "label": "Properties", "icon": "panel.svg", "default_key": "Tab"},
        
        # File
        {"id": "file.save", "label": "Save", "icon": "save.svg", "default_key": "Ctrl+S"}
    ]
}

# B. The UI Layout (Where things go)
# Defines the toolbar and context menus.
layout_default = {
    "toolbar": {
        "visible": True,
        "items": [
            {"command": "file.save"},
            {"separator": True},
            {"command": "edit.undo"},
            {"command": "edit.redo"},
            {"separator": True},
            {"command": "tool.wire_mode"},
            {"command": "tool.measure"},
            {"separator": True},
            {"command": "view.zoom_extents"},
            {"command": "view.toggle_props"}
        ]
    },
    "context_menu": {
        "device": [
            {"command": "edit.move"},
            {"command": "edit.rotate_cw"},
            {"separator": True},
            {"command": "edit.delete", "style": "danger"}
        ],
        "wire": [
            {"command": "edit.delete"},
            {"separator": True},
            {"command": "tool.measure"}
        ]
    }
}

# C. The Visual Theme (Colors & Grid)
theme_default = {
    "canvas": {
        "background_color": "#2E2E2E",
        "grid": {
            "minor_spacing_mm": 5.0,
            "major_spacing_mm": 25.0,
            "minor_color": "#444444",
            "major_color": "#666666",
            "minor_opacity": 0.3,
            "major_opacity": 0.6
        },
        "interaction": {
            "selection_halo": "#FFD166",
            "active_drag": "#EF476F"
        }
    }
}

# D. The Library (Physical Physics)
wires_default = {
    "wires": {
        "TXL-18": {
            "family": "SAE J1128 TXL",
            "gauge": "18AWG",
            "od_mm": 2.18,
            "resistance_ohm_m": 0.021,
            "weight_g_m": 9.6
        },
        "TXL-20": {
            "family": "SAE J1128 TXL",
            "gauge": "20AWG",
            "od_mm": 1.90,
            "resistance_ohm_m": 0.033,
            "weight_g_m": 7.2
        }
    }
}

parts_default = {
    "parts": {
        "CONN-DT-2S": {
            "manufacturer": "TE Connectivity",
            "part_number": "DT06-2S",
            "description": "2-Way Plug, Deutsch DT",
            "ip_rating": "IP68"
        }
    }
}

# E. Validation Rules
electrical_rules = {
    "rules": [
        {
            "id": "ELEC_001",
            "name": "Voltage Drop Critical",
            "target": "wire",
            "severity": "error",
            "check": "((length_mm / 1000) * library.resistance_ohm_m * load_amps) > 1.0",
            "message": "Voltage drop exceeds 1.0V critical limit"
        }
    ]
}

# ==========================================
# 2. EXECUTION
# ==========================================

structure = {
    "resources/config/actions.yaml": actions_default,
    "resources/config/ui_layout.yaml": layout_default,
    "resources/config/theme.yaml": theme_default,
    "resources/library/wires.yaml": wires_default,
    "resources/library/parts.yaml": parts_default,
    "resources/rules/electrical.yaml": electrical_rules,
}

def build_resources():
    # ...removed debug print...
    
    # 1. Create Directories
    dirs = [
        ".cache/render", 
        ".cache/routing", 
        ".cache/bom",
        "resources/config", 
        "resources/library", 
        "resources/rules"
    ]
    for folder in dirs:
        os.makedirs(folder, exist_ok=True)
        # ...removed debug print...

    # 2. Write Defaults (Only if missing, to preserve user edits!)
    for filepath, data in structure.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                yaml.dump(data, f, sort_keys=False, default_flow_style=False)
            # ...removed debug print...
        else:
            # ...removed debug print...

    # 3. Update .gitignore
    gitignore_path = ".gitignore"
    cache_entry = "\n# System Cache\n.cache/\n"
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
        if ".cache/" not in content:
            with open(gitignore_path, "a") as f2:
                f2.write(cache_entry)
            # ...removed debug print...
    else:
        with open(gitignore_path, "w") as f:
            f.write(cache_entry)
        # ...removed debug print...

if __name__ == "__main__":
    build_resources()
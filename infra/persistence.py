"""
YAMLPersistence / JSONPersistence: Project/Session Persistence Utilities
-----------------------------------------------------

Usage:
    from infra.persistence import YAMLPersistence, JSONPersistence
    YAMLPersistence.save(harness, 'file.yaml')
    harness = YAMLPersistence.load('file.yaml')
    JSONPersistence.save(harness, 'file.json')
    harness = JSONPersistence.load('file.json')

Backup/Restore:
    - YAMLPersistence.backup_file('file.yaml') creates a timestamped backup.
    - YAMLPersistence.list_backups('file.yaml') lists available backups.
    - YAMLPersistence.restore_backup('file.yaml', backup_path) restores from backup.

Schema/Versioning:
    - Each file includes a __schema_version__ for migration.
    - Add migration functions to YAMLPersistence.MIGRATIONS as needed.

Maintenance:
    - Extend to support new formats or migration logic as needed.
    - For advanced use, subclass or extend methods.
"""
import yaml
import json
from pathlib import Path
from core.models import Harness

class JSONPersistence:
    """
    Handles persistence of Harness objects to and from JSON files.
    Includes schema versioning for migration support.
    """
    SCHEMA_VERSION = "2026-01"

    @staticmethod
    def save(harness: Harness, file_path: Path):
        """
        Save a Harness object to a JSON file, including schema version.
        Args:
            harness (Harness): The harness object to save.
            file_path (Path): The file path to save the JSON to.
        """
        data = harness.to_dict()
        data['__schema_version__'] = JSONPersistence.SCHEMA_VERSION
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(file_path: Path) -> Harness:
        """
        Load a Harness object from a JSON file, including schema version check.
        Args:
            file_path (Path): The file path to load the JSON from.
        Returns:
            Harness: The loaded harness object.
        Raises:
            ValueError: If the schema version is missing.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
            schema_version = data.pop('__schema_version__', None)
            if schema_version is None:
                raise ValueError("Missing __schema_version__ in JSON file. Migration required.")
            # For now, skip migration for JSON (could add if needed)
        return Harness.from_dict(data)

class YAMLPersistence:
    """
    Handles persistence of Harness objects to and from YAML files.
    Supports schema versioning, migration, and backup/restore utilities.
    """
    SCHEMA_VERSION = "2026-01"
    # Migration registry: maps from old version to migration function
    MIGRATIONS = {}

    @staticmethod
    def backup_file(file_path: Path, retention: int = 10):
        """
        Create a timestamped backup of the given file. Retain only the latest N backups.
        Args:
            file_path (Path): The file to back up.
            retention (int): Number of backups to retain.
        Returns:
            Path: The path to the backup file created, or None if source file doesn't exist.
        """
        import shutil
        import datetime
        file_path = Path(file_path)  # Accept str or Path
        if not file_path.exists():
            return None
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = file_path.parent / f"{file_path.name}.bak-{ts}"
        shutil.copy2(file_path, backup_path)
        # Prune old backups
        backups = sorted(file_path.parent.glob(f"{file_path.name}.bak-*"), reverse=True)
        for old in backups[retention:]:
            try:
                old.unlink()
            except Exception:
                pass
        return backup_path

    @staticmethod
    def list_backups(file_path: Path):
        """
        List available backups for the given file, sorted newest first.
        Args:
            file_path (Path): The file to list backups for.
        Returns:
            list: List of backup file paths.
        """
        file_path = Path(file_path)
        backups = sorted(file_path.parent.glob(f"{file_path.name}.bak-*"), reverse=True)
        return backups

    @staticmethod
    def restore_backup(file_path: Path, backup_path: Path):
        """
        Restore the file from a selected backup.
        Args:
            file_path (Path): The file to restore.
            backup_path (Path): The backup file to restore from.
        """
        import shutil
        file_path = Path(file_path)
        backup_path = Path(backup_path)
        shutil.copy2(backup_path, file_path)

    @staticmethod
    def save(harness: Harness, file_path: Path, backup: bool = True, retention: int = 10):
        """
        Save a Harness object to a YAML file, including bundles and schema version.
        All references (bundle_ids, wire_ids, etc.) are serialized as UUID strings only - never as embedded objects.
        Args:
            harness (Harness): The harness object to save.
            file_path (Path): The file path to save the YAML to.
            backup (bool): If True, create a versioned backup before saving.
            retention (int): Number of backups to retain.
        """
        if backup:
            YAMLPersistence.backup_file(file_path, retention=retention)
        file_path = Path(file_path)
        data = harness.to_dict()
        data['__schema_version__'] = YAMLPersistence.SCHEMA_VERSION
        with open(file_path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    @staticmethod
    def register_migration(from_version, migration_fn):
        """
        Register a migration function for a specific schema version.
        Args:
            from_version (str): The version to migrate from.
            migration_fn (callable): The migration function.
        """
        YAMLPersistence.MIGRATIONS[from_version] = migration_fn

    @staticmethod
    def migrate(data, from_version, to_version):
        """
        Apply migrations stepwise from from_version to to_version.
        Args:
            data (dict): The data to migrate.
            from_version (str): The starting version.
            to_version (str): The target version.
        Returns:
            dict: The migrated data.
        Raises:
            ValueError: If no migration path exists.
        """
        current = from_version
        while current != to_version:
            if current not in YAMLPersistence.MIGRATIONS:
                raise ValueError(f"No migration path from {current} to {to_version}")
            data, next_version = YAMLPersistence.MIGRATIONS[current](data)
            current = next_version
        return data

    @staticmethod
    def load(file_path: Path) -> Harness:
        """
        Load a Harness object from a YAML file, including bundles and schema version check.
        Args:
            file_path (Path): The file path to load the YAML from.
        Returns:
            Harness: The loaded harness object.
        Raises:
            ValueError: If the schema version is incompatible or missing.
        """
        file_path = Path(file_path)
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            schema_version = data.pop('__schema_version__', None)
            if schema_version is None:
                raise ValueError("Missing __schema_version__ in YAML file. Migration required.")
            if schema_version != YAMLPersistence.SCHEMA_VERSION:
                # Try to migrate stepwise to current version
                data = YAMLPersistence.migrate(data, schema_version, YAMLPersistence.SCHEMA_VERSION)
        harness = Harness.from_dict(data)
        _snap_rotated_devices(harness)
        return harness


def _snap_rotated_devices(harness):
    """Post-load fixup: snap rotated devices so their first pin lands on grid."""
    import math
    try:
        from api.manager import APIManager
        grid = APIManager.get_instance().settings.grid_size_mm
    except Exception:
        grid = 2.54
    if grid <= 0:
        return
    for device in getattr(harness, 'devices', []):
        rotation = getattr(device, 'rotation', 0.0)
        pins = getattr(device, 'pins', [])
        if rotation == 0.0 or not pins:
            continue
        pin = pins[0]
        meta = getattr(device, 'meta', {}) or {}
        width = meta.get('width_mm', 40.0)
        height = meta.get('height_mm', 30.0)
        margin_x = (width % grid) / 2.0
        margin_y = (height % grid) / 2.0
        ox = -margin_x + width / 2.0
        oy = -margin_y + height / 2.0
        rad = math.radians(rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        dx = pin.x - ox
        dy = pin.y - oy
        rpx = round(cos_r * dx + sin_r * dy + ox, 4)
        rpy = round(-sin_r * dx + cos_r * dy + oy, 4)
        pin_scene_x = device.x + rpx
        pin_scene_y = device.y + rpy
        snapped_x = round(pin_scene_x / grid) * grid
        snapped_y = round(pin_scene_y / grid) * grid
        adj_x = snapped_x - pin_scene_x
        adj_y = snapped_y - pin_scene_y
        if abs(adj_x) > 1e-6 or abs(adj_y) > 1e-6:
            device.x = round(device.x + adj_x, 4)
            device.y = round(device.y + adj_y, 4)


# Example migration registration (for future use):
# def migrate_2025_12_to_2026_01(data):
#     # ... migration logic ...
#     return data, "2026-01"
# YAMLPersistence.register_migration("2025-12", migrate_2025_12_to_2026_01)


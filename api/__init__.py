class TalusAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # Import Pin and Wire before Harness.model_rebuild
            from core.pin import Pin
            from core.wire import Wire
            from core.models import Harness
            Harness.model_rebuild()
            from api.manager import APIManager
            self._manager = APIManager.get_instance()

    def import_netlist(self, csv_path):
        """
        Imports a netlist CSV and creates Wire entities in the Core harness.
        """
        import csv
        from core.models import Wire
        harness = self._manager.context.harness
        # Ensure wires dict exists in meta
        if "wires" not in harness.meta:
            harness.meta["wires"] = {}
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                wire_id = row["wire_id"]
                source_pin = row["source_pin"]
                target_pin = row["target_pin"]
                gauge_mm = float(row.get("gauge_mm", 1.0))
                wire = Wire(
                    id=wire_id,
                    source_pin_id=source_pin,
                    target_pin_id=target_pin,
                    path_nodes=[],
                    status="UNDEFINED"
                )
                harness.meta["wires"][wire_id] = wire

    def get_harness(self):
        """
        Returns the current Core harness object.
        """
        return self._manager.context.harness

# Singleton accessor
api = TalusAPI()

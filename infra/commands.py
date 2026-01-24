"""
Command pattern implementation for undoable actions in Talus Trace.
Defines base and concrete command classes for transactional operations.
"""
from abc import ABC, abstractmethod
from typing import Any, Tuple
from abc import ABC, abstractmethod
from typing import Any, Tuple

class BaseCommand(ABC):
    """
    Abstract base class for all command transactions in Talus Trace Infra.
    Implements optimistic locking via base_revision.
    """
    base_revision: int

    @abstractmethod
    def execute(self, target_entity: Any) -> bool:
        """
        Execute the command on the target entity.
        Returns True if successful, raises Exception on failure.
        """
        pass


class MoveDeviceCommand(BaseCommand):
    """
    Specific implementation for moving a Device in mm space.
    """
    def __init__(self, device_id: str, new_pos: Tuple[float, float], base_revision: int):
        """
        Initialize the command with required parameters.
        Args:
            device_id (str): The device identifier.
            new_pos (Tuple[float, float]): New position in mm.
            base_revision (int): Revision for optimistic locking.
        """
        self.device_id = device_id
        self.new_pos = new_pos
        self.base_revision = base_revision

    def execute(self, target_entity: Any) -> bool:
        """
        Updates target position and increments revision after validating the lock.
        """
        # Optimistic locking: check revision
        current_rev = getattr(target_entity, 'revision', None)
        if current_rev != self.base_revision:
            raise Exception(f"Revision mismatch: expected {self.base_revision} but got {current_rev}")
        # Update position (mm) and increment revision
        if hasattr(self, 'new_pos') and isinstance(self.new_pos, (list, tuple)) and len(self.new_pos) == 2:
            target_entity.x = self.new_pos[0]
            target_entity.y = self.new_pos[1]
        target_entity.revision += 1
        return True
        target_entity.revision += 1
        return True


class CommandManager:
    """
    Infrastructure controller that executes commands against entities.
    """
    def execute(self, command: BaseCommand, target_entity: Any) -> bool:
        """
        Primary entry point for executing mutations.
        """
        return command.execute(target_entity)
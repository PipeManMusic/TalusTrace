"""
WizardManager: Wizard/Assistant State Management
-----------------------------------------------

Usage:
    from infra.wizard_manager import WizardManager
    wiz = WizardManager(['step1', 'step2', 'step3'])
    wiz.start()
    wiz.next()
    wiz.set_data('step1', {'foo': 'bar'})
    state = wiz.serialize()
    wiz2 = WizardManager.deserialize(state)

- Supports step tracking, data storage, and persistence.

Maintenance:
    - Extend for more complex workflows or branching logic.
    - For advanced use, subclass WizardManager or extend its methods.
"""
import json

class WizardManager:
    """
    Manages wizard/assistant state, step tracking, and data storage for workflows.
    Supports serialization and restoration of wizard progress and data.
    """
    def __init__(self, steps):
        """
        Initialize the WizardManager with a list of steps.
        Args:
            steps (list): List of step identifiers.
        """
        self.steps = list(steps)
        self.current = 0
        self.data = {step: {} for step in self.steps}
        self.active = False

    def start(self):
        """
        Start the wizard and set the current step to the first.
        """
        self.current = 0
        self.active = True

    def next(self):
        """
        Advance to the next step in the wizard.
        Deactivates wizard if last step is reached.
        """
        if self.current < len(self.steps) - 1:
            self.current += 1
            if self.current == len(self.steps) - 1:
                self.active = False
        else:
            self.active = False

    def prev(self):
        """
        Go back to the previous step in the wizard.
        """
        if self.current > 0:
            self.current -= 1

    def set_data(self, step, data):
        """
        Set data for a specific step.
        Args:
            step (str): Step identifier.
            data (dict): Data to associate with the step.
        """
        if step in self.data:
            self.data[step] = data

    def get_data(self, step):
        """
        Get data for a specific step.
        Args:
            step (str): Step identifier.
        Returns:
            dict: Data associated with the step.
        """
        return self.data.get(step, {})

    def serialize(self):
        """
        Serialize the wizard state to a JSON string.
        Returns:
            str: The serialized state.
        """
        return json.dumps({
            'steps': self.steps,
            'current': self.current,
            'data': self.data,
            'active': self.active
        })

    @classmethod
    def deserialize(cls, state):
        """
        Deserialize a JSON string to restore wizard state.
        Args:
            state (str): The serialized state string.
        Returns:
            WizardManager: The restored instance.
        """
        obj = json.loads(state)
        wiz = cls(obj['steps'])
        wiz.current = obj['current']
        wiz.data = obj['data']
        wiz.active = obj['active']
        return wiz

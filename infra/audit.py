"""
Audit engine and rule definitions for Talus Trace.
Provides background audit logic, rule evaluation, and violation reporting.
"""
import os
import yaml
from pydantic import BaseModel, Field
from typing import Optional, Literal, List

from core.logic import check_bundle_constraints, find_wire_overlaps

# Minimal Rule for test
class Rule:
    """Represents an audit rule with an ID, check expression, and message."""
    def __init__(self, id, check, message, severity="WARNING", field_check=None):
        """
        Initialize a Rule.
        Args:
            id (str): Rule identifier.
            check (str): Legacy expression (kept for backward compat).
            message (str): Message to display on violation.
            severity (str): WARNING, ERROR, or INFO.
            field_check (dict): Declarative field-based check definition.
        """
        self.id = id
        self.check = check
        self.message = message
        self.severity = severity
        self.field_check = field_check

class Violation(BaseModel):
    """Strict typing for design flaws (PH3-3.1)."""
    target_id: str
    severity: Literal["WARNING", "ERROR", "INFO"]
    message: str
    category: Optional[str] = "ENGINEERING"

def _evaluate_field_check(wire, field_check) -> bool:
    """
    Evaluate a declarative field_check against a wire.
    Returns True if the check triggers a violation.
    """
    # Conditional guard: only check if 'when' condition is met
    when = field_check.get('when')
    if when:
        if not _evaluate_field_check(wire, when):
            return False

    field = field_check.get('field', '')
    operator = field_check.get('operator', 'eq')
    expected = field_check.get('value')
    actual = getattr(wire, field, None)

    if operator == 'eq':
        return actual == expected
    elif operator == 'neq':
        return actual != expected
    elif operator == 'empty':
        return not actual  # None, '', 0, False all count as empty
    elif operator == 'not_empty':
        return bool(actual)
    elif operator == 'gt':
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False
    elif operator == 'lt':
        try:
            return float(actual) < float(expected)
        except (TypeError, ValueError):
            return False
    return False


# Cache of parsed rules keyed by resolved path -> (mtime, rules)
_RULES_CACHE: dict = {}


def load_rules_from_yaml(path: str = None) -> List[Rule]:
    """
    Load audit rules from the electrical.yaml rules file.
    Returns a list of Rule objects.

    Results are cached per resolved path (keyed by the file's modification
    time) so that repeated audits triggered by model changes do not re-read
    and re-parse the YAML from disk on the UI thread.
    """
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "resources", "rules", "electrical.yaml")
    if not os.path.exists(path):
        return []
    mtime = os.path.getmtime(path)
    cached = _RULES_CACHE.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    with open(path, 'r') as f:
        data = yaml.safe_load(f) or {}
    rules = []
    for entry in data.get('rules', []):
        if not entry:
            continue
        rules.append(Rule(
            id=entry.get('id', ''),
            check=entry.get('check', ''),
            message=entry.get('message', ''),
            severity=entry.get('severity', 'WARNING').upper(),
            field_check=entry.get('field_check'),
        ))
    _RULES_CACHE[path] = (mtime, rules)
    return rules


class AuditEngine:
    """
    Executes background audits via Thread Pool (PH3-1.1).
    Runs rules and full audits on the harness model.
    """
    def __init__(self, rules=None):
        """
        Initialize the AuditEngine with optional rules.
        Args:
            rules: List of Rule objects to evaluate. If None, loads from YAML.
        """
        if rules is not None:
            self.rules = rules
        else:
            self.rules = load_rules_from_yaml()

    def run(self, harness) -> List[Violation]:
        """
        Run all rules against all wires in the harness.
        Args:
            harness: The harness model to audit.
        Returns:
            List of Violation objects.
        """
        violations = []
        for rule in self.rules:
            for wire in getattr(harness, 'wires', []):
                triggered = False
                if rule.field_check:
                    triggered = _evaluate_field_check(wire, rule.field_check)
                elif rule.check:
                    # Legacy eval path (kept for backward compat with old rules)
                    try:
                        triggered = bool(eval(rule.check, {}, {**wire.__dict__}))
                    except Exception:
                        continue
                if triggered:
                    violations.append(Violation(
                        target_id=getattr(wire, 'id', ''),
                        severity=rule.severity,
                        message=rule.message,
                        category="ENGINEERING",
                    ))
        return violations

    def run_full_audit(self, harness_model) -> List[Violation]:
        """
        Run a full audit on the harness model, including topology scanning.
        Args:
            harness_model: The harness model to audit.
        Returns:
            List[Violation]: List of detected violations.
        """
        violations = []

        # 1. Run field-based wire rules
        violations.extend(self.run(harness_model))

        # 2. Bundle constraint scanning
        all_wires = getattr(harness_model, 'wires', [])
        if all_wires:
            existing_bundles = getattr(harness_model, 'bundles', None)
            groups = find_wire_overlaps(all_wires, existing_bundles=existing_bundles)
            for group in groups:
                diameters = []
                for wid in group.wire_ids:
                    for w in all_wires:
                        if getattr(w, 'id', None) == wid:
                            diameters.append(getattr(w, 'diameter_mm', 1.0))
                            break
                    else:
                        diameters.append(1.0)
                issue = check_bundle_constraints(diameters)
                if issue:
                    violations.append(Violation(
                        target_id=f"BUNDLE_{group.key}",
                        **issue
                    ))

        return violations
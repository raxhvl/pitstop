"""Compare gas schedules."""

from dataclasses import dataclass
from typing import Any

from models.schema import ResolvedSchedule


@dataclass
class DictDiff:
    """Differences between two dictionaries."""

    changed: dict[str, tuple[Any, Any]]  # key -> (old_value, new_value)
    added: dict[str, Any]  # key -> value
    removed: dict[str, Any]  # key -> value

    def is_empty(self) -> bool:
        """Check if there are no differences."""
        return not self.changed and not self.added and not self.removed


@dataclass
class ScheduleComparison:
    """Comparison result between two schedules."""

    schedule1_name: str
    schedule2_name: str
    fork_changed: tuple[str, str] | None  # (old_fork, new_fork) or None
    eips_changed: tuple[list[str], list[str]] | None  # (old_eips, new_eips) or None
    operations: DictDiff
    storage: DictDiff
    precompiles: DictDiff
    memory: DictDiff
    calldata: DictDiff

    def has_differences(self) -> bool:
        """Check if there are any differences."""
        return (
            self.fork_changed is not None
            or self.eips_changed is not None
            or not self.operations.is_empty()
            or not self.storage.is_empty()
            or not self.precompiles.is_empty()
            or not self.memory.is_empty()
            or not self.calldata.is_empty()
        )


def _diff_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> DictDiff:
    """Compare two dictionaries and return differences.

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        DictDiff containing changed, added, and removed items
    """
    changed = {}
    added = {}
    removed = {}

    all_keys = set(dict1.keys()) | set(dict2.keys())

    for key in all_keys:
        if key in dict1 and key in dict2:
            if dict1[key] != dict2[key]:
                changed[key] = (dict1[key], dict2[key])
        elif key in dict2:
            added[key] = dict2[key]
        else:
            removed[key] = dict1[key]

    return DictDiff(changed=changed, added=added, removed=removed)


def compare_schedules(
    schedule1: ResolvedSchedule, schedule2: ResolvedSchedule, name1: str, name2: str
) -> ScheduleComparison:
    """Compare two resolved schedules.

    Args:
        schedule1: First resolved schedule
        schedule2: Second resolved schedule
        name1: Name of first schedule (fork name)
        name2: Name of second schedule (fork name)

    Returns:
        ScheduleComparison with all differences
    """
    fork_changed = None
    if schedule1.fork != schedule2.fork:
        fork_changed = (schedule1.fork, schedule2.fork)

    eips_changed = None
    if schedule1.eips != schedule2.eips:
        eips_changed = (schedule1.eips, schedule2.eips)

    return ScheduleComparison(
        schedule1_name=name1,
        schedule2_name=name2,
        fork_changed=fork_changed,
        eips_changed=eips_changed,
        operations=_diff_dicts(schedule1.opcodes, schedule2.opcodes),
        storage=_diff_dicts(schedule1.storage, schedule2.storage),
        precompiles=_diff_dicts(schedule1.precompiles, schedule2.precompiles),
        memory=_diff_dicts(schedule1.memory, schedule2.memory),
        calldata=_diff_dicts(schedule1.calldata, schedule2.calldata),
    )

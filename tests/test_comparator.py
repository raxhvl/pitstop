"""Tests for schedule comparison."""

import pytest

from core.comparator import compare_schedules, _diff_dicts, DictDiff
from schedules.schema import GasSchedule


@pytest.fixture
def schedule1():
    """Create first test schedule."""
    return GasSchedule(
        fork="prague",
        description="Prague schedule",
        operations={"BASE": 2, "LOW": 5, "REMOVED": 10},
        storage={"SLOAD": 2100},
        precompiles={"ECRECOVER": 3000},
        memory={"MEMORY": 3},
    )


@pytest.fixture
def schedule2():
    """Create second test schedule (with changes)."""
    return GasSchedule(
        fork="osaka",
        description="Osaka schedule",
        operations={"BASE": 3, "LOW": 5, "ADDED": 20},  # BASE changed, REMOVED gone, ADDED new
        storage={"SLOAD": 2100},  # No change
        precompiles={"ECRECOVER": 2500},  # Changed
        memory={"MEMORY": 3},  # No change
    )


@pytest.fixture
def identical_schedule():
    """Create identical schedule to schedule1."""
    return GasSchedule(
        fork="prague",
        description="Prague schedule",
        operations={"BASE": 2, "LOW": 5, "REMOVED": 10},
        storage={"SLOAD": 2100},
        precompiles={"ECRECOVER": 3000},
        memory={"MEMORY": 3},
    )


def test_diff_dicts_no_changes():
    """Test diffing identical dictionaries."""
    dict1 = {"a": 1, "b": 2}
    dict2 = {"a": 1, "b": 2}

    diff = _diff_dicts(dict1, dict2)

    assert diff.is_empty()
    assert len(diff.changed) == 0
    assert len(diff.added) == 0
    assert len(diff.removed) == 0


def test_diff_dicts_changed():
    """Test diffing dictionaries with changed values."""
    dict1 = {"a": 1, "b": 2}
    dict2 = {"a": 10, "b": 2}

    diff = _diff_dicts(dict1, dict2)

    assert not diff.is_empty()
    assert diff.changed == {"a": (1, 10)}
    assert len(diff.added) == 0
    assert len(diff.removed) == 0


def test_diff_dicts_added():
    """Test diffing dictionaries with added items."""
    dict1 = {"a": 1}
    dict2 = {"a": 1, "b": 2}

    diff = _diff_dicts(dict1, dict2)

    assert not diff.is_empty()
    assert len(diff.changed) == 0
    assert diff.added == {"b": 2}
    assert len(diff.removed) == 0


def test_diff_dicts_removed():
    """Test diffing dictionaries with removed items."""
    dict1 = {"a": 1, "b": 2}
    dict2 = {"a": 1}

    diff = _diff_dicts(dict1, dict2)

    assert not diff.is_empty()
    assert len(diff.changed) == 0
    assert len(diff.added) == 0
    assert diff.removed == {"b": 2}


def test_diff_dicts_mixed():
    """Test diffing dictionaries with all types of changes."""
    dict1 = {"a": 1, "b": 2, "c": 3}
    dict2 = {"a": 10, "b": 2, "d": 4}

    diff = _diff_dicts(dict1, dict2)

    assert not diff.is_empty()
    assert diff.changed == {"a": (1, 10)}
    assert diff.added == {"d": 4}
    assert diff.removed == {"c": 3}


def test_compare_identical_schedules(schedule1, identical_schedule):
    """Test comparing identical schedules."""
    comparison = compare_schedules(schedule1, identical_schedule, "schedule1", "identical")

    assert not comparison.has_differences()
    assert comparison.fork_changed is None
    assert comparison.description_changed is None
    assert comparison.operations.is_empty()
    assert comparison.storage.is_empty()
    assert comparison.precompiles.is_empty()
    assert comparison.memory.is_empty()


def test_compare_different_schedules(schedule1, schedule2):
    """Test comparing different schedules."""
    comparison = compare_schedules(schedule1, schedule2, "prague", "osaka")

    assert comparison.has_differences()
    assert comparison.schedule1_name == "prague"
    assert comparison.schedule2_name == "osaka"

    # Fork changed
    assert comparison.fork_changed == ("prague", "osaka")

    # Description changed
    assert comparison.description_changed == ("Prague schedule", "Osaka schedule")

    # Operations: BASE changed, REMOVED gone, ADDED new
    assert not comparison.operations.is_empty()
    assert comparison.operations.changed == {"BASE": (2, 3)}
    assert comparison.operations.added == {"ADDED": 20}
    assert comparison.operations.removed == {"REMOVED": 10}

    # Storage: no change
    assert comparison.storage.is_empty()

    # Precompiles: ECRECOVER changed
    assert not comparison.precompiles.is_empty()
    assert comparison.precompiles.changed == {"ECRECOVER": (3000, 2500)}

    # Memory: no change
    assert comparison.memory.is_empty()


def test_compare_only_fork_different():
    """Test comparing schedules with only fork different."""
    s1 = GasSchedule(
        fork="prague",
        description="Same",
        operations={"BASE": 2},
        storage={"SLOAD": 100},
        precompiles={"ECRECOVER": 3000},
        memory={"MEMORY": 3},
    )
    s2 = GasSchedule(
        fork="osaka",
        description="Same",
        operations={"BASE": 2},
        storage={"SLOAD": 100},
        precompiles={"ECRECOVER": 3000},
        memory={"MEMORY": 3},
    )

    comparison = compare_schedules(s1, s2, "s1", "s2")

    assert comparison.has_differences()
    assert comparison.fork_changed == ("prague", "osaka")
    assert comparison.description_changed is None
    assert comparison.operations.is_empty()

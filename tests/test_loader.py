"""Tests for schedule loading."""

import pytest

from core.loader import load_schedule
from schedules.schema import GasSchedule


def test_load_prague_schedule():
    """Test loading the prague schedule."""
    schedule = load_schedule("prague")

    assert isinstance(schedule, GasSchedule)
    assert schedule.fork == "prague"
    # Verify required sections exist
    assert len(schedule.operations) > 0
    assert len(schedule.storage) > 0
    assert len(schedule.precompiles) > 0
    assert len(schedule.memory) > 0


def test_load_nonexistent_schedule():
    """Test loading a non-existent schedule raises error."""
    with pytest.raises(FileNotFoundError, match="Schedule not found"):
        load_schedule("nonexistent")


def test_loaded_schedule_validation():
    """Test that loaded schedules are validated."""
    schedule = load_schedule("prague")

    # Verify types are correct after validation
    assert isinstance(schedule.operations, dict)
    assert isinstance(schedule.storage, dict)
    assert isinstance(schedule.precompiles, dict)
    assert isinstance(schedule.memory, dict)

    # Verify values are integers
    for cost in schedule.operations.values():
        assert isinstance(cost, int)

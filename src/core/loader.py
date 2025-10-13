"""Load and validate gas schedules from YAML files."""

from pathlib import Path

import yaml

import schedules
from schedules.schema import GasSchedule


def load_schedule(schedule_name: str) -> GasSchedule:
    """Load a gas schedule by name.

    Args:
        schedule_name: Name of the schedule (without .yaml extension)

    Returns:
        Validated GasSchedule object

    Raises:
        FileNotFoundError: If schedule file doesn't exist
        ValidationError: If schedule data is invalid
    """
    # Find schedule file in the schedules package directory
    schedules_dir = Path(schedules.__file__).parent
    schedule_path = schedules_dir / f"{schedule_name}.yaml"

    if not schedule_path.exists():
        raise FileNotFoundError(f"Schedule not found: {schedule_path}")

    with open(schedule_path) as f:
        data = yaml.safe_load(f)

    return GasSchedule(**data)

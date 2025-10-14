"""Tests for code generators."""

from pathlib import Path

import pytest

from core.verifier import verify_file
from generators import get_generator
from schedules.schema import GasSchedule


@pytest.fixture
def sample_schedule():
    """Create a sample gas schedule for testing."""
    return GasSchedule(
        fork="test",
        description="Test schedule",
        operations={"BASE": 2, "JUMPDEST": 1},
        storage={"SLOAD": 2100, "SSTORE_SET": 20000},
        precompiles={"ECRECOVER": 3000},
        memory={"MEMORY": 3, "KECCAK256": 30},
    )


def test_get_geth_generator():
    """Test getting Geth generator."""
    generator = get_generator("geth")
    assert generator.client_name == "geth"
    assert generator.file_extension == ".go"


def test_get_unknown_generator():
    """Test getting unknown generator raises error."""
    with pytest.raises(ValueError, match="Unknown client"):
        get_generator("unknown")


def test_generate_string(sample_schedule):
    """Test generating code as string."""
    generator = get_generator("geth")
    code = generator.generate_string(sample_schedule)

    # Verify code is not empty
    assert len(code) > 0
    assert isinstance(code, str)


def test_generate_file(sample_schedule, tmp_path):
    """Test generating code to file."""
    generator = get_generator("geth")
    output_file = tmp_path / "gas.go"

    generator.generate(sample_schedule, output_file)

    # Verify file was created
    assert output_file.exists()

    # Verify content matches expected output using verifier
    expected_code = generator.generate_string(sample_schedule)
    matches, diff = verify_file(expected_code, output_file)
    assert matches, f"Generated file doesn't match expected output:\n{diff}"


def test_generate_creates_directory(sample_schedule, tmp_path):
    """Test that generate creates parent directories if needed."""
    generator = get_generator("geth")
    output_file = tmp_path / "nested" / "dir" / "gas.go"

    generator.generate(sample_schedule, output_file)

    assert output_file.exists()
    assert output_file.parent.exists()

    # Verify content matches using verifier
    expected_code = generator.generate_string(sample_schedule)
    matches, diff = verify_file(expected_code, output_file)
    assert matches, f"Generated file doesn't match expected output:\n{diff}"

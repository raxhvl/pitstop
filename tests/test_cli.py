"""Tests for CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.cli import pitstop


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


def test_pitstop_help(cli_runner):
    """Test pitstop help command."""
    result = cli_runner.invoke(pitstop, ["--help"])
    assert result.exit_code == 0
    # Verify both commands are listed
    assert "swap" in result.output
    assert "check" in result.output


def test_swap_command(cli_runner, tmp_path):
    """Test swap command generates code."""
    output_file = tmp_path / "gas.go"

    result = cli_runner.invoke(pitstop, ["swap", "geth", "prague", str(output_file)])

    assert result.exit_code == 0
    assert "Generated geth code" in result.output
    assert "🏁" in result.output
    assert output_file.exists()

    # Verify content using verifier
    from core.loader import load_schedule
    from core.verifier import verify_file
    from generators import get_generator

    generator = get_generator("geth")
    schedule = load_schedule("prague")
    expected_code = generator.generate_string(schedule)
    matches, diff = verify_file(expected_code, output_file)
    assert matches, f"Generated file doesn't match expected output:\n{diff}"


def test_swap_invalid_extension(cli_runner, tmp_path):
    """Test swap command with invalid file extension."""
    output_file = tmp_path / "gas.txt"

    result = cli_runner.invoke(pitstop, ["swap", "geth", "prague", str(output_file)])

    assert result.exit_code == 1
    assert "must have .go extension" in result.output


def test_swap_invalid_schedule(cli_runner, tmp_path):
    """Test swap command with non-existent schedule."""
    output_file = tmp_path / "gas.go"

    result = cli_runner.invoke(
        pitstop, ["swap", "geth", "nonexistent", str(output_file)]
    )

    assert result.exit_code == 1
    assert "Error" in result.output


def test_check_command_matching(cli_runner, tmp_path):
    """Test check command with matching file."""
    output_file = tmp_path / "gas.go"

    # First generate a file
    result = cli_runner.invoke(pitstop, ["swap", "geth", "prague", str(output_file)])
    assert result.exit_code == 0

    # Now check it matches
    result = cli_runner.invoke(pitstop, ["check", "geth", "prague", str(output_file)])

    assert result.exit_code == 0
    assert "File verified" in result.output
    assert "✓" in result.output


def test_check_command_modified(cli_runner, tmp_path):
    """Test check command with modified file."""
    output_file = tmp_path / "gas.go"

    # First generate a file
    result = cli_runner.invoke(pitstop, ["swap", "geth", "prague", str(output_file)])
    assert result.exit_code == 0

    # Modify the file
    with open(output_file, "a") as f:
        f.write("\n// Modified\n")

    # Check should fail
    result = cli_runner.invoke(pitstop, ["check", "geth", "prague", str(output_file)])

    assert result.exit_code == 1
    assert "Modified" in result.output


def test_check_invalid_extension(cli_runner, tmp_path):
    """Test check command with invalid file extension."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    result = cli_runner.invoke(pitstop, ["check", "geth", "prague", str(test_file)])

    assert result.exit_code == 1
    assert "must have .go extension" in result.output


def test_check_missing_file(cli_runner):
    """Test check command with non-existent file."""
    result = cli_runner.invoke(
        pitstop, ["check", "geth", "prague", "/nonexistent/file.go"]
    )

    assert result.exit_code == 2  # Click's error code for invalid path

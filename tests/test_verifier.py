"""Tests for code verification."""

from pathlib import Path

import pytest

from core.verifier import verify_file


def test_verify_matching_file(tmp_path):
    """Test verification of matching file."""
    expected_code = "package vm\n\nconst GasBase = 2\n"
    test_file = tmp_path / "test.go"
    test_file.write_text(expected_code)

    matches, diff = verify_file(expected_code, test_file)

    assert matches is True
    assert diff == ""


def test_verify_modified_file(tmp_path):
    """Test verification of modified file."""
    expected_code = "package vm\n\nconst GasBase = 2\n"
    actual_code = "package vm\n\nconst GasBase = 3\n"
    test_file = tmp_path / "test.go"
    test_file.write_text(actual_code)

    matches, diff = verify_file(expected_code, test_file)

    assert matches is False
    assert diff != ""
    assert "GasBase = 2" in diff
    assert "GasBase = 3" in diff


def test_verify_missing_file(tmp_path):
    """Test verification of non-existent file."""
    expected_code = "package vm\n"
    test_file = tmp_path / "nonexistent.go"

    matches, diff = verify_file(expected_code, test_file)

    assert matches is False
    assert "File not found" in diff


def test_verify_diff_shows_line_context(tmp_path):
    """Test that diff shows proper context."""
    expected_code = "line1\nline2\nline3\n"
    actual_code = "line1\nmodified\nline3\n"
    test_file = tmp_path / "test.txt"
    test_file.write_text(actual_code)

    matches, diff = verify_file(expected_code, test_file)

    assert matches is False
    assert "line2" in diff
    assert "modified" in diff

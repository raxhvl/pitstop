"""Verify generated code matches expected output."""

import difflib
from pathlib import Path


def verify_file(expected_code: str, file_path: Path) -> tuple[bool, str]:
    """Verify if a file matches expected generated code.

    Args:
        expected_code: The expected code content
        file_path: Path to the file to verify

    Returns:
        Tuple of (matches: bool, diff: str)
        - matches: True if content matches, False otherwise
        - diff: Empty string if matches, unified diff otherwise
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    actual_code = file_path.read_text()

    if expected_code == actual_code:
        return True, ""

    # Generate unified diff
    expected_lines = expected_code.splitlines(keepends=True)
    actual_lines = actual_code.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile=f"expected ({file_path.name})",
        tofile=f"actual ({file_path.name})",
        lineterm="",
    )

    return False, "".join(diff)

"""Nethermind code generator."""

from .base import BaseGenerator


class NethermindGenerator(BaseGenerator):
    """Generator for Nethermind (C#) client code."""

    def __init__(self):
        """Initialize Nethermind generator."""
        super().__init__("nethermind")

    @property
    def file_extension(self) -> str:
        """Return the expected file extension."""
        return ".cs"

    def get_template_name(self) -> str:
        """Return the name of the template file."""
        return "GasCostOf.cs.jinja2"

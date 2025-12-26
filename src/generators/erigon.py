"""Erigon code generator."""

from .base import BaseGenerator


class ErigonGenerator(BaseGenerator):
    """Generator for Erigon (Go) client code."""

    def __init__(self):
        """Initialize Erigon generator."""
        super().__init__("erigon")

    @property
    def file_extension(self) -> str:
        """Return the expected file extension."""
        return ".go"

    def get_template_name(self) -> str:
        """Return the name of the template file."""
        return "protocol.go.jinja2"

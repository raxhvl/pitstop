"""Geth code generator."""

from .base import BaseGenerator


class GethGenerator(BaseGenerator):
    """Generator for Geth (Go) client code."""

    def __init__(self):
        """Initialize Geth generator."""
        super().__init__("geth")

    @property
    def file_extension(self) -> str:
        """Return the expected file extension."""
        return ".go"

    def get_template_name(self) -> str:
        """Return the name of the template file."""
        return "protocol_params.go.jinja2"

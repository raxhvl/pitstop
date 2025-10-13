"""Base generator class for client code generation."""

from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from schedules.schema import GasSchedule


class BaseGenerator(ABC):
    """Base class for client code generators."""

    def __init__(self, client_name: str):
        """Initialize generator.

        Args:
            client_name: Name of the client (e.g., 'geth')
        """
        self.client_name = client_name
        # Find templates directory relative to this file
        templates_dir = Path(__file__).parent.parent / "templates" / client_name
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            keep_trailing_newline=True,
        )

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the expected file extension (e.g., '.go', '.rs')."""
        pass

    @abstractmethod
    def get_template_name(self) -> str:
        """Return the name of the template file."""
        pass

    def generate(self, schedule: GasSchedule, output_path: Path) -> None:
        """Generate client code from schedule.

        Args:
            schedule: Validated gas schedule
            output_path: Path to write generated code
        """
        template = self.env.get_template(self.get_template_name())
        code = template.render(schedule=schedule)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)

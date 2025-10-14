"""Base generator class for client code generation."""

from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Environment, PackageLoader

from core.config import PITSTOP_HEADER
from schedules.schema import GasSchedule


class BaseGenerator(ABC):
    """Base class for client code generators."""

    def __init__(self, client_name: str):
        """Initialize generator.

        Args:
            client_name: Name of the client (e.g., 'geth')
        """
        self.client_name = client_name
        self.env = Environment(
            loader=PackageLoader("templates", client_name),
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

    def generate_string(self, schedule: GasSchedule) -> str:
        """Generate client code from schedule as a string.

        Args:
            schedule: Validated gas schedule

        Returns:
            Generated code as string
        """
        template = self.env.get_template(self.get_template_name())
        return template.render(
            schedule=schedule,
            pitstop_header=PITSTOP_HEADER,
        )

    def generate(self, schedule: GasSchedule, output_path: Path) -> None:
        """Generate client code from schedule.

        Args:
            schedule: Validated gas schedule
            output_path: Path to write generated code
        """
        code = self.generate_string(schedule)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)

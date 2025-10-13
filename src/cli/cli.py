"""CLI for pitstop."""

from pathlib import Path

import click

from core.loader import load_schedule
from generators import get_generator


@click.group()
def pitstop():
    """Pitstop - Swap Ethereum config across clients."""
    pass


@pitstop.command()
@click.argument("client", type=click.Choice(["geth"]), metavar="CLIENT")
@click.argument("schedule", metavar="SCHEDULE")
@click.argument("output_path", type=click.Path(), metavar="OUTPUT_PATH")
def swap(client: str, schedule: str, output_path: str):
    """Generate client code from a gas schedule.

    Args:
        client: Client name (currently only 'geth' supported)
        schedule: Name of the schedule (without .yaml extension)
        output_path: Path to write generated code
    """
    try:
        # Get generator for client
        generator = get_generator(client)

        # Validate file extension
        output_file = Path(output_path)
        if output_file.suffix != generator.file_extension:
            click.echo(
                f"Error: Output file for {client} must have {generator.file_extension} extension",
                err=True
            )
            raise click.Abort()

        # Load and validate schedule
        gas_schedule = load_schedule(schedule)

        # Generate code
        generator.generate(gas_schedule, output_file)

        click.echo(f"✓ Generated {client} code: {output_path}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    pitstop()

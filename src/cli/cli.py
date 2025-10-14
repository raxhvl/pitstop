"""CLI for pitstop."""

from pathlib import Path

import click

from core.loader import load_schedule
from core.verifier import verify_file
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

        click.echo(f"🏁 Generated {client} code: {output_path}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@pitstop.command()
@click.argument("client", type=click.Choice(["geth"]), metavar="CLIENT")
@click.argument("schedule", metavar="SCHEDULE")
@click.argument("file_path", type=click.Path(exists=True), metavar="FILE_PATH")
def check(client: str, schedule: str, file_path: str):
    """Verify a file matches the expected generated code.

    Args:
        client: Client name (currently only 'geth' supported)
        schedule: Name of the schedule (without .yaml extension)
        file_path: Path to the file to verify
    """
    try:
        # Get generator for client
        generator = get_generator(client)

        # Validate file extension
        file = Path(file_path)
        if file.suffix != generator.file_extension:
            click.echo(
                f"Error: File for {client} must have {generator.file_extension} extension",
                err=True
            )
            raise click.Abort()

        # Load and validate schedule
        gas_schedule = load_schedule(schedule)

        # Generate expected code
        expected_code = generator.generate_string(gas_schedule)

        # Verify file
        matches, diff = verify_file(expected_code, file)

        if matches:
            click.echo(f"✓ File verified: {file_path}")
        else:
            click.echo(f"Modified: {file_path}", err=True)
            if diff:
                click.echo("\n" + diff, err=True)
            raise click.Abort()

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

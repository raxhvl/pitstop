"""CLI for pitstop."""

from pathlib import Path

import click

from core.comparator import compare_schedules
from core.loader import load_schedule
from core.verifier import verify_file
from generators import get_generator


@click.group()
def pitstop():
    """Pitstop - Swap Ethereum config across clients."""
    pass


@pitstop.command()
@click.argument("client", type=click.Choice(["geth", "nethermind"]), metavar="CLIENT")
@click.argument("schedule", metavar="SCHEDULE")
@click.argument("output_path", type=click.Path(), metavar="OUTPUT_PATH")
def swap(client: str, schedule: str, output_path: str):
    """Generate client code from a gas schedule.

    Args:
        client: Client name ('geth' or 'nethermind')
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
@click.argument("client", type=click.Choice(["geth", "nethermind"]), metavar="CLIENT")
@click.argument("schedule", metavar="SCHEDULE")
@click.argument("file_path", type=click.Path(exists=True), metavar="FILE_PATH")
def check(client: str, schedule: str, file_path: str):
    """Verify a file matches the expected generated code.

    Args:
        client: Client name ('geth' or 'nethermind')
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


@pitstop.command()
@click.argument("schedule1", metavar="SCHEDULE1")
@click.argument("schedule2", metavar="SCHEDULE2")
def compare(schedule1: str, schedule2: str):
    """Compare two gas schedules.

    Args:
        schedule1: Name of the first schedule (without .yaml extension)
        schedule2: Name of the second schedule (without .yaml extension)
    """
    try:
        # Load both schedules
        gas_schedule1 = load_schedule(schedule1)
        gas_schedule2 = load_schedule(schedule2)

        # Compare schedules
        comparison = compare_schedules(gas_schedule1, gas_schedule2, schedule1, schedule2)

        # If identical
        if not comparison.has_differences():
            click.echo(f"✓ Schedules match perfectly")
            return

        # Show differences
        click.echo(f"Comparing {schedule1} vs {schedule2}\n")

        # Show fork/description changes
        if comparison.fork_changed:
            old_fork, new_fork = comparison.fork_changed
            click.echo(f"Fork: {old_fork} → {new_fork}")

        if comparison.description_changed:
            old_desc, new_desc = comparison.description_changed
            click.echo(f'Description: "{old_desc}" → "{new_desc}"')

        if comparison.fork_changed or comparison.description_changed:
            click.echo()

        # Helper to display section differences
        def show_section(title: str, diff):
            if diff.is_empty():
                return

            click.echo(f"{title}:")
            for key, (old_val, new_val) in sorted(diff.changed.items()):
                click.echo(f"  {key}: {old_val} → {new_val}")
            for key, val in sorted(diff.added.items()):
                click.echo(f"  + {key}: {val}")
            for key, val in sorted(diff.removed.items()):
                click.echo(f"  - {key}: {val}")
            click.echo()

        # Show each section
        show_section("Operations", comparison.operations)
        show_section("Storage", comparison.storage)
        show_section("Precompiles", comparison.precompiles)
        show_section("Memory", comparison.memory)

        # Count total changes
        total_changed = sum([
            len(comparison.operations.changed),
            len(comparison.storage.changed),
            len(comparison.precompiles.changed),
            len(comparison.memory.changed),
        ])
        total_added = sum([
            len(comparison.operations.added),
            len(comparison.storage.added),
            len(comparison.precompiles.added),
            len(comparison.memory.added),
        ])
        total_removed = sum([
            len(comparison.operations.removed),
            len(comparison.storage.removed),
            len(comparison.precompiles.removed),
            len(comparison.memory.removed),
        ])

        # Summary
        parts = []
        if total_changed:
            parts.append(f"{total_changed} changed")
        if total_added:
            parts.append(f"{total_added} added")
        if total_removed:
            parts.append(f"{total_removed} removed")

        click.echo(f"✓ {', '.join(parts)}")

        # Exit with code 1 to indicate differences (like diff command)
        raise click.Abort()

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    pitstop()

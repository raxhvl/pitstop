"""CLI for pitstop."""

from pathlib import Path

import click

from core.comparator import compare_schedules
from core.resolver import resolve_fork
from core.verifier import verify_file
from generators import get_generator


@click.group()
def pitstop():
    """Pitstop - Swap Ethereum config across clients."""
    pass


@pitstop.command()
@click.argument("client", type=click.Choice(["erigon", "geth", "nethermind"]), metavar="CLIENT")
@click.argument("fork", metavar="FORK")
@click.argument("output_path", type=click.Path(), metavar="OUTPUT_PATH")
def swap(client: str, fork: str, output_path: str):
    """Generate client code from a fork.

    Args:
        client: Client name ('erigon', 'geth', or 'nethermind')
        fork: Name of the fork (e.g., 'frontier', 'prague')
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

        # Resolve fork to get schedule
        schedule = resolve_fork(fork)

        # Generate code
        generator.generate(schedule, output_file)

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
@click.argument("client", type=click.Choice(["erigon", "geth", "nethermind"]), metavar="CLIENT")
@click.argument("fork", metavar="FORK")
@click.argument("file_path", type=click.Path(exists=True), metavar="FILE_PATH")
def check(client: str, fork: str, file_path: str):
    """Verify a file matches the expected generated code.

    Args:
        client: Client name ('erigon', 'geth', or 'nethermind')
        fork: Name of the fork (e.g., 'frontier', 'prague')
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

        # Resolve fork to get schedule
        schedule = resolve_fork(fork)

        # Generate expected code
        expected_code = generator.generate_string(schedule)

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
@click.argument("fork1", metavar="FORK1")
@click.argument("fork2", metavar="FORK2")
def compare(fork1: str, fork2: str):
    """Compare two forks.

    Args:
        fork1: Name of the first fork (e.g., 'frontier', 'prague')
        fork2: Name of the second fork (e.g., 'frontier', 'prague')
    """
    try:
        # Resolve both forks
        schedule1 = resolve_fork(fork1)
        schedule2 = resolve_fork(fork2)

        # Compare schedules
        comparison = compare_schedules(schedule1, schedule2, fork1, fork2)

        # If identical
        if not comparison.has_differences():
            click.echo(f"✓ Schedules match perfectly")
            return

        # Show differences
        click.echo(f"Comparing {fork1} vs {fork2}\n")

        # Show fork/eips changes
        if comparison.fork_changed:
            old_fork, new_fork = comparison.fork_changed
            click.echo(f"Fork: {old_fork} → {new_fork}")

        if comparison.eips_changed:
            old_eips, new_eips = comparison.eips_changed
            click.echo(f"EIPs: {old_eips} → {new_eips}")

        if comparison.fork_changed or comparison.eips_changed:
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
        show_section("Calldata", comparison.calldata)

        # Count total changes
        total_changed = sum([
            len(comparison.operations.changed),
            len(comparison.storage.changed),
            len(comparison.precompiles.changed),
            len(comparison.memory.changed),
            len(comparison.calldata.changed),
        ])
        total_added = sum([
            len(comparison.operations.added),
            len(comparison.storage.added),
            len(comparison.precompiles.added),
            len(comparison.memory.added),
            len(comparison.calldata.added),
        ])
        total_removed = sum([
            len(comparison.operations.removed),
            len(comparison.storage.removed),
            len(comparison.precompiles.removed),
            len(comparison.memory.removed),
            len(comparison.calldata.removed),
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

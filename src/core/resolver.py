"""Fork resolution with constant resolution and EIP merging."""

import yaml
from pathlib import Path
from functools import lru_cache

from models.schema import EIP, Fork, ResolvedSchedule, GasCosts, Value


# Paths
EIPS_DIR = Path("schedules/eips")
FORKS_FILE = Path("schedules/forks.yaml")


class ResolutionError(Exception):
    """Error during fork or constant resolution."""
    pass


@lru_cache(maxsize=128)
def load_eip(eip_id: str) -> EIP:
    """
    Load an EIP from schedules/eips/{eip_id}.yaml

    Args:
        eip_id: EIP identifier (e.g., 'frontier', '150', 'research.cheap_sload')

    Returns:
        Parsed EIP model

    Raises:
        ResolutionError: If EIP file not found or invalid
    """
    eip_path = EIPS_DIR / f"{eip_id}.yaml"

    if not eip_path.exists():
        raise ResolutionError(
            f"EIP not found: {eip_id}\n"
            f"Expected file: {eip_path}\n"
            f"Available EIPs: {', '.join(get_available_eips())}"
        )

    try:
        with open(eip_path) as f:
            data = yaml.safe_load(f)
        return EIP(**data)
    except Exception as e:
        raise ResolutionError(f"Error loading EIP {eip_id}: {e}") from e


@lru_cache(maxsize=1)
def load_forks() -> dict[str, Fork]:
    """
    Load all fork definitions from schedules/forks.yaml

    Returns:
        Dictionary mapping fork names to Fork models

    Raises:
        ResolutionError: If forks file not found or invalid
    """
    if not FORKS_FILE.exists():
        raise ResolutionError(f"Forks file not found: {FORKS_FILE}")

    try:
        with open(FORKS_FILE) as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or "forks" not in data:
            raise ResolutionError("forks.yaml must contain 'forks' key")

        return {name: Fork(**fork_data) for name, fork_data in data["forks"].items()}
    except Exception as e:
        raise ResolutionError(f"Error loading forks: {e}") from e


def get_available_eips() -> list[str]:
    """Get list of available EIP IDs."""
    if not EIPS_DIR.exists():
        return []
    return [p.stem for p in EIPS_DIR.glob("*.yaml")]


def get_fork_ancestry(fork_name: str) -> list[str]:
    """
    Get ordered list of fork names from root to specified fork.

    Args:
        fork_name: Fork name to get ancestry for

    Returns:
        List of fork names in order from root to fork_name

    Example:
        get_fork_ancestry('cancun') -> ['frontier', 'homestead', ..., 'cancun']

    Raises:
        ResolutionError: If fork not found or cycle detected
    """
    forks = load_forks()

    if fork_name not in forks:
        raise ResolutionError(
            f"Fork not found: {fork_name}\n"
            f"Available forks: {', '.join(forks.keys())}"
        )

    ancestry = []
    seen = set()
    current = fork_name

    while current is not None:
        if current in seen:
            raise ResolutionError(
                f"Cycle detected in fork chain: {' -> '.join(ancestry + [current])}"
            )

        seen.add(current)
        ancestry.append(current)

        fork = forks[current]
        current = fork.extends

    return list(reversed(ancestry))


def get_eip_chain(fork_name: str) -> list[str]:
    """
    Get ordered list of EIP IDs to apply for a fork.

    Args:
        fork_name: Fork name

    Returns:
        Ordered list of EIP IDs from base to most recent

    Raises:
        ResolutionError: If fork not found or invalid
    """
    forks = load_forks()
    ancestry = get_fork_ancestry(fork_name)

    eip_chain = []
    for ancestor in ancestry:
        fork = forks[ancestor]
        eip_chain.extend(fork.eips)

    return eip_chain


def merge_constants(base: dict[str, int], override: dict[str, int]) -> dict[str, int]:
    """
    Merge two constant dictionaries (last-wins).

    Args:
        base: Base constants
        override: Override constants

    Returns:
        Merged constants dictionary
    """
    result = base.copy()
    result.update(override)
    return result


def resolve_value(value: Value, constants: dict[str, int]) -> int:
    """
    Resolve a value that might be a constant reference.

    Args:
        value: Either an int or $CONSTANT reference
        constants: Available constants for resolution

    Returns:
        Resolved integer value

    Raises:
        ResolutionError: If constant reference not found
    """
    if isinstance(value, int):
        return value

    if isinstance(value, str) and value.startswith("$"):
        const_name = value[1:]  # Remove $ prefix
        if const_name not in constants:
            raise ResolutionError(
                f"Constant ${const_name} not found in merged constants.\n"
                f"Available constants: {', '.join(constants.keys())}"
            )
        return constants[const_name]

    # Value is a plain string not starting with $
    raise ResolutionError(
        f"Invalid value: {value}. Expected int or $CONSTANT reference."
    )


def resolve_gas_costs(gas_costs: GasCosts, constants: dict[str, int]) -> GasCosts:
    """
    Resolve all constant references in gas costs.

    Args:
        gas_costs: Gas costs with possible $CONSTANT references
        constants: Merged constants for resolution

    Returns:
        GasCosts with all constants resolved to integers
    """
    resolved_opcodes = {
        name: resolve_value(value, constants)
        for name, value in gas_costs.opcodes.items()
    }

    resolved_precompiles = {
        name: {
            key: resolve_value(val, constants)
            for key, val in precompile.items()
        }
        for name, precompile in gas_costs.precompiles.items()
    }

    resolved_storage = {
        name: resolve_value(value, constants)
        for name, value in gas_costs.storage.items()
    }

    resolved_calldata = {
        name: resolve_value(value, constants)
        for name, value in gas_costs.calldata.items()
    }

    resolved_transaction = {
        name: resolve_value(value, constants)
        for name, value in gas_costs.transaction.items()
    }

    resolved_memory = {
        name: resolve_value(value, constants)
        for name, value in gas_costs.memory.items()
    }

    return GasCosts(
        opcodes=resolved_opcodes,
        precompiles=resolved_precompiles,
        storage=resolved_storage,
        calldata=resolved_calldata,
        transaction=resolved_transaction,
        memory=resolved_memory,
    )


def merge_gas_costs(base: GasCosts, override: GasCosts) -> GasCosts:
    """
    Merge two GasCosts (last-wins for each category).

    Args:
        base: Base gas costs
        override: Override gas costs

    Returns:
        Merged gas costs
    """
    merged_opcodes = {**base.opcodes, **override.opcodes}
    merged_precompiles = {**base.precompiles, **override.precompiles}
    merged_storage = {**base.storage, **override.storage}
    merged_calldata = {**base.calldata, **override.calldata}
    merged_transaction = {**base.transaction, **override.transaction}
    merged_memory = {**base.memory, **override.memory}

    return GasCosts(
        opcodes=merged_opcodes,
        precompiles=merged_precompiles,
        storage=merged_storage,
        calldata=merged_calldata,
        transaction=merged_transaction,
        memory=merged_memory,
    )


def resolve_fork(fork_name: str) -> ResolvedSchedule:
    """
    Resolve a fork into its complete configuration.

    Algorithm:
    1. Get EIP chain for fork (base + all ancestor EIPs)
    2. Merge all constants (last-wins)
    3. Merge all gas_costs sections (last-wins)
    4. Resolve $CONSTANT references using merged constants
    5. Return ResolvedSchedule

    Args:
        fork_name: Fork name to resolve

    Returns:
        Resolved schedule with all constants resolved

    Raises:
        ResolutionError: If resolution fails

    Example:
        schedule = resolve_fork('homestead')
        # schedule.opcodes['SLOAD'] == 200 (after applying base + 150)
    """
    eip_chain = get_eip_chain(fork_name)

    # Step 1 & 2: Merge all constants
    merged_constants: dict[str, int] = {}
    for eip_id in eip_chain:
        eip = load_eip(eip_id)
        merged_constants = merge_constants(merged_constants, eip.constants)

    # Step 3: Merge all gas_costs sections (before resolution)
    merged_gas_costs = GasCosts()
    for eip_id in eip_chain:
        eip = load_eip(eip_id)
        merged_gas_costs = merge_gas_costs(merged_gas_costs, eip.gas_costs)

    # Step 4: Resolve $CONSTANT references
    resolved_gas_costs = resolve_gas_costs(merged_gas_costs, merged_constants)

    # Step 5: Get fork ancestry for since() checks
    ancestry = get_fork_ancestry(fork_name)

    # Step 6: Create ResolvedSchedule with ancestry
    schedule = ResolvedSchedule(
        fork=fork_name,
        eips=eip_chain,
        constants=merged_constants,
        gas_costs=resolved_gas_costs,
        fork_ancestry=ancestry,
    )

    return schedule

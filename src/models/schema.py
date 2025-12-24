"""Pydantic models for EIP-based configuration validation.
This module defines the schema for EIP-centric configuration changes.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Core type for values that can be literal or constant references
Value = int | str  # Either a literal integer or $CONSTANT reference

# Type aliases for different configuration sections
ConstantsMap = dict[str, int]
OpcodesMap = dict[str, Value]
PrecompileMap = dict[str, Value]  # {BASE: value, WORD: value, ...}
PrecompilesMap = dict[str, PrecompileMap]
StorageMap = dict[str, Value]
CalldataMap = dict[str, Value]
TransactionMap = dict[str, Value]
MemoryMap = dict[str, Value]


class GasCosts(BaseModel):
    """Gas costs organized by category.

    Note: Future config types (e.g., consensus params) will have similar
    category-based organization.
    """

    opcodes: OpcodesMap = Field(
        default_factory=dict, description="Opcode gas costs (ordered by hex)"
    )
    precompiles: PrecompilesMap = Field(
        default_factory=dict, description="Precompile gas costs (ordered by address)"
    )
    storage: StorageMap = Field(
        default_factory=dict, description="Storage costs (non-opcode)"
    )
    calldata: CalldataMap = Field(
        default_factory=dict, description="Calldata costs (per-byte)"
    )
    transaction: TransactionMap = Field(
        default_factory=dict, description="Transaction-level costs"
    )
    memory: MemoryMap = Field(
        default_factory=dict, description="Memory expansion and copy costs"
    )


class EIP(BaseModel):
    """EIP definition specifying configuration changes.

    Each EIP file describes what changed in the protocol, with constants
    for reusable values and categorized configuration values.
    """

    name: str = Field(..., description="Human-readable description of changes")
    constants: ConstantsMap = Field(
        default_factory=dict,
        description="Reusable constants (use $CONSTANT to reference)",
    )
    gas_costs: GasCosts = Field(
        default_factory=GasCosts, description="Gas cost changes by category"
    )


class Fork(BaseModel):
    """Fork definition composing EIPs.

    Forks are named collections of EIPs with optional inheritance,
    allowing incremental protocol evolution.
    """

    extends: Optional[str] = Field(None, description="Parent fork name for inheritance")
    eips: list[str] = Field(..., description="Ordered list of EIP IDs to apply")


class ResolvedSchedule(BaseModel):
    """Resolved configuration after merging all EIPs in fork ancestry.

    This represents the final, flattened state after applying:
    1. Base EIP + all ancestor fork EIPs (via extends chain)
    2. Constant resolution ($CONSTANT references)
    3. Last-wins merge for conflicting values
    """

    fork: str = Field(..., description="Fork name")
    eips: list[str] = Field(..., description="Ordered list of applied EIP IDs")
    constants: ConstantsMap = Field(
        ..., description="Merged constants after resolution"
    )
    gas_costs: GasCosts = Field(..., description="Merged and resolved configuration")
    fork_ancestry: list[str] = Field(default_factory=list, description="Fork ancestry chain for since() checks")

    # Property accessors for convenience
    @property
    def opcodes(self) -> dict[str, int]:
        """Get opcode costs."""
        return self.gas_costs.opcodes

    @property
    def precompiles(self) -> dict[str, dict[str, int]]:
        """Get precompile costs."""
        return self.gas_costs.precompiles

    @property
    def storage(self) -> dict[str, int]:
        """Get storage costs."""
        return self.gas_costs.storage

    @property
    def calldata(self) -> dict[str, int]:
        """Get calldata costs."""
        return self.gas_costs.calldata

    @property
    def transaction(self) -> dict[str, int]:
        """Get transaction costs."""
        return self.gas_costs.transaction

    @property
    def memory(self) -> dict[str, int]:
        """Get memory costs."""
        return self.gas_costs.memory

    def since(self, fork_name: str) -> bool:
        """
        Check if fork is in this schedule's ancestry chain.

        This enables conditional logic in templates for fork-specific features.

        Args:
            fork_name: Fork name to check (e.g., 'cancun', 'homestead')

        Returns:
            True if fork_name is in ancestry, False otherwise

        Example:
            {% if schedule.since('cancun') %}
                // Cancun-specific features
            {% endif %}
        """
        return fork_name in self.fork_ancestry

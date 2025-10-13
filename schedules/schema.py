"""Pydantic models for gas schedule validation."""

from pydantic import BaseModel, Field


class GasSchedule(BaseModel):
    """Gas schedule definition."""

    fork: str = Field(..., description="Fork name")
    description: str = Field(..., description="Schedule description")
    operations: dict[str, int] = Field(..., description="Operation gas costs")
    storage: dict[str, int] = Field(..., description="Storage gas costs")
    precompiles: dict[str, int] = Field(..., description="Precompile gas costs")
    memory: dict[str, int] = Field(..., description="Memory gas costs")

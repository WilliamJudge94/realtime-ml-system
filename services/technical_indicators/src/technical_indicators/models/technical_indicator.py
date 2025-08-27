"""
Technical indicator data model.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class TechnicalIndicator(BaseModel):
    """
    Represents a technical indicator calculated from candle data.
    """
    
    # Inherited from candle
    pair: str = Field(..., description="Currency pair (e.g., 'BTC/USD')")
    window_start_ms: int = Field(..., description="Start time of the window in milliseconds")
    window_end_ms: int = Field(..., description="End time of the window in milliseconds")
    
    # Technical indicator specific fields
    indicator_name: str = Field(..., description="Name of the technical indicator (e.g., 'SMA', 'RSI')")
    indicator_value: float = Field(..., description="Calculated value of the indicator")
    period: Optional[int] = Field(None, description="Period used for calculation (e.g., 14 for RSI-14)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the indicator")
    
    @field_validator("pair")
    @classmethod
    def validate_pair(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError("pair must be at least 3 characters")
        if "/" not in v:
            raise ValueError("pair must contain '/' separator")
        return v.upper()
    
    @field_validator("window_start_ms", "window_end_ms")
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        if v < 0:
            raise ValueError("timestamp must be non-negative")
        return v
    
    @field_validator("indicator_name")
    @classmethod
    def validate_indicator_name(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError("indicator_name cannot be empty")
        return v.upper()
    
    @field_validator("period")
    @classmethod
    def validate_period(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("period must be positive")
        return v
    
    def model_post_init(self, __context) -> None:
        """Validate business rules after model creation."""
        if self.window_start_ms >= self.window_end_ms:
            raise ValueError("window_start_ms must be less than window_end_ms")
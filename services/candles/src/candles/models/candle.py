"""
Simple candle model using pydantic.
"""

from typing import Dict, Any

from pydantic import BaseModel, field_validator, model_validator

from .exceptions import CandleError


class Candle(BaseModel):
    """Simple candle data structure with basic validation."""
    pair: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    window_start_ms: int
    window_end_ms: int
    candle_seconds: int
    schema_version: str = "1.0"
    
    @field_validator('open', 'high', 'low', 'close')
    @classmethod
    def validate_prices(cls, v: float) -> float:
        if v <= 0:
            raise CandleError(f"Price must be positive: {v}")
        return v
    
    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v: float) -> float:
        if v < 0:
            raise CandleError(f"Volume cannot be negative: {v}")
        return v
    
    @field_validator('candle_seconds')
    @classmethod
    def validate_candle_seconds(cls, v: int) -> int:
        if v <= 0:
            raise CandleError("Candle seconds must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_ohlc_and_window(self) -> 'Candle':
        """Validate OHLC relationships and window constraints."""
        # OHLC consistency
        if self.high < self.low:
            raise CandleError(f"High {self.high} cannot be less than low {self.low}")
        
        if not (self.low <= self.open <= self.high):
            raise CandleError(f"Open {self.open} must be between low {self.low} and high {self.high}")
        
        if not (self.low <= self.close <= self.high):
            raise CandleError(f"Close {self.close} must be between low {self.low} and high {self.high}")
        
        # Window validation
        if self.window_end_ms <= self.window_start_ms:
            raise CandleError("Window end must be after start")
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Kafka output."""
        data = self.model_dump()
        # Convert float values to strings as required by the original implementation
        for field in ['open', 'high', 'low', 'close', 'volume']:
            data[field] = str(data[field])
        return data
    
    @classmethod
    def from_aggregation(cls, candle_data: Dict[str, Any], window_info: Dict[str, Any]) -> 'Candle':
        """Create Candle from QuixStreams aggregation result."""
        try:
            combined_data = {
                **candle_data,
                **window_info,
                'candle_seconds': window_info.get('candle_seconds', 60)
            }
            return cls(**combined_data)
        except Exception as e:
            raise CandleError(f"Failed to create candle: {e}") from e
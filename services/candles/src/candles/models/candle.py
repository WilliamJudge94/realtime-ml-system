"""
Minimal candle output model for consistent formatting.

Provides a simple schema for candle output without over-engineering.
"""

from decimal import Decimal
from typing import Dict, Any

from pydantic import BaseModel, Field, field_validator

from .exceptions import ValidationError


class CandleOutput(BaseModel):
    """
    Simple candle output model matching the structure from previous_main.py.
    
    Provides consistent output format and basic validation without
    complex state management.
    """
    
    # Core OHLCV data (matches previous_main.py output)
    pair: str = Field(..., description="Trading pair")
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="Highest price")
    low: Decimal = Field(..., description="Lowest price")
    close: Decimal = Field(..., description="Closing price")
    volume: Decimal = Field(..., ge=0, description="Total volume")
    
    # Window information
    window_start_ms: int = Field(..., description="Window start timestamp (ms)")
    window_end_ms: int = Field(..., description="Window end timestamp (ms)")
    candle_seconds: int = Field(..., gt=0, description="Candle duration in seconds")
    
    # Schema versioning for compatibility
    schema_version: str = Field(default="1.0", description="Output schema version")
    
    class Config:
        """Pydantic model configuration."""
        extra = "forbid"  # Strict output schema
        json_encoders = {
            Decimal: lambda v: str(v),
        }
    
    @field_validator('high', 'low', 'open', 'close')
    @classmethod
    def validate_prices_positive(cls, v: Decimal) -> Decimal:
        """Ensure all prices are positive."""
        if v <= 0:
            raise ValidationError(f"Price must be positive: {v}")
        return v
    
    @field_validator('window_end_ms')
    @classmethod
    def validate_window_order(cls, v: int, info) -> int:
        """Ensure window end is after start."""
        if 'window_start_ms' in info.data and v <= info.data['window_start_ms']:
            raise ValidationError("Window end must be after start")
        return v
    
    def validate_ohlc_consistency(self) -> None:
        """Validate OHLC price relationships."""
        if self.high < self.low:
            raise ValidationError(f"High {self.high} cannot be less than low {self.low}")
        
        if self.open > self.high or self.open < self.low:
            raise ValidationError(f"Open {self.open} must be between high and low")
        
        if self.close > self.high or self.close < self.low:
            raise ValidationError(f"Close {self.close} must be between high and low")
    
    def to_kafka_message(self) -> Dict[str, Any]:
        """Convert to dictionary for Kafka output."""
        return {
            "pair": self.pair,
            "open": str(self.open),
            "high": str(self.high), 
            "low": str(self.low),
            "close": str(self.close),
            "volume": str(self.volume),
            "window_start_ms": self.window_start_ms,
            "window_end_ms": self.window_end_ms,
            "candle_seconds": self.candle_seconds,
            "schema_version": self.schema_version,
        }
    
    @classmethod
    def from_aggregation_result(cls, candle_data: Dict[str, Any], window_info: Dict[str, Any]) -> 'CandleOutput':
        """Create CandleOutput from QuixStreams aggregation result.
        
        This matches the structure used in previous_main.py:
        - candle_data: the 'value' from aggregation (OHLCV)
        - window_info: window start/end and metadata
        """
        try:
            # Handle Decimal conversion
            for field in ['open', 'high', 'low', 'close', 'volume']:
                if field in candle_data and not isinstance(candle_data[field], Decimal):
                    candle_data[field] = Decimal(str(candle_data[field]))
            
            output = cls(
                pair=candle_data['pair'],
                open=candle_data['open'],
                high=candle_data['high'],
                low=candle_data['low'],
                close=candle_data['close'],
                volume=candle_data['volume'],
                window_start_ms=window_info['window_start_ms'],
                window_end_ms=window_info['window_end_ms'],
                candle_seconds=window_info.get('candle_seconds', 60),
            )
            
            # Validate OHLC consistency
            output.validate_ohlc_consistency()
            
            return output
            
        except Exception as e:
            raise ValidationError(f"Failed to create candle output: {e}") from e
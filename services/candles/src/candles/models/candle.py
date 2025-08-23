"""
Simple candle model using dataclasses.
"""

from dataclasses import dataclass
from typing import Dict, Any

from .exceptions import CandleError


@dataclass
class Candle:
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
    
    def __post_init__(self):
        """Validate OHLC relationships and basic constraints."""
        # Positive price validation
        for field in ['open', 'high', 'low', 'close']:
            value = getattr(self, field)
            if value <= 0:
                raise CandleError(f"{field} must be positive: {value}")
        
        # Non-negative volume
        if self.volume < 0:
            raise CandleError(f"Volume cannot be negative: {self.volume}")
        
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
        
        if self.candle_seconds <= 0:
            raise CandleError("Candle seconds must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
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
    def from_aggregation(cls, candle_data: Dict[str, Any], window_info: Dict[str, Any]) -> 'Candle':
        """Create Candle from QuixStreams aggregation result."""
        try:
            return cls(
                pair=candle_data['pair'],
                open=float(candle_data['open']),
                high=float(candle_data['high']),
                low=float(candle_data['low']),
                close=float(candle_data['close']),
                volume=float(candle_data['volume']),
                window_start_ms=window_info['window_start_ms'],
                window_end_ms=window_info['window_end_ms'],
                candle_seconds=window_info.get('candle_seconds', 60),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise CandleError(f"Failed to create candle: {e}") from e
"""
Lightweight domain models for the candles service.

Provides essential validation and formatting for trade processing
and candle output without over-engineering.
"""

from .exceptions import (
    CandleProcessingError,
    InvalidTradeError,
    ValidationError,
)
from .trade import TradeMessage
from .candle import CandleOutput

__all__ = [
    # Exceptions
    "CandleProcessingError",
    "InvalidTradeError", 
    "ValidationError",
    # Models
    "TradeMessage",
    "CandleOutput",
]
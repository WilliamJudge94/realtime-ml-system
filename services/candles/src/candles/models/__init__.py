"""
Simplified domain models for the candles service.
"""

from .exceptions import CandleError
from .trade import Trade
from .candle import Candle

__all__ = ['Trade', 'Candle', 'CandleError']
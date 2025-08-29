import numpy as np
from typing import Dict, Optional
from loguru import logger
from talib import stream

from config.config import Settings


def compute_technical_indicators(
    candle: Dict,
    state: Dict,
    settings: Optional[Settings] = None,
) -> Dict:
    """
    Computes technical indicators from the candles in the state dictionary.

    Args:
        candle (dict): Latest candle data
        state (dict): State dictionary containing list of candles

    Returns:
        dict: Dictionary with the computed technical indicators
    """

    # Extract the candles from the state dictionary
    candles = state.get('candles', default=[])

    logger.debug(f'Number of candles in state: {len(candles)}')

    # Validate minimum data requirements
    if len(candles) < 2:
        logger.warning("Insufficient data for technical indicators - need at least 2 candles")
        return {**candle}

    # Use provided settings or load if not provided (for backward compatibility)
    if settings is None:
        from config.config import load_settings
        settings = load_settings()

    try:
        # Validate required fields and extract arrays
        required_fields = ['open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if not all(field in c for c in candles):
                logger.error(f"Missing required field '{field}' in candle data")
                return {**candle}
        
        # Extract the open, close, high, low, volume candles (which is a list of dictionaries)
        # into numpy arrays, because this is the type that TA-Lib expects to compute the indicators
        _open = np.array([c['open'] for c in candles])
        _high = np.array([c['high'] for c in candles])
        _low = np.array([c['low'] for c in candles])
        close = np.array([c['close'] for c in candles])
        volume = np.array([c['volume'] for c in candles])

        indicators = {}

        # Simple Moving Average (SMA) for configured periods
        for period in settings.sma_periods:
            if len(candles) >= period:
                indicators[f'sma_{period}'] = stream.SMA(close, timeperiod=period)

        # Exponential Moving Average (EMA) for configured periods
        for period in settings.ema_periods:
            if len(candles) >= period:
                indicators[f'ema_{period}'] = stream.EMA(close, timeperiod=period)

        # Relative Strength Index (RSI) for configured periods
        for period in settings.rsi_periods:
            if len(candles) >= period:
                indicators[f'rsi_{period}'] = stream.RSI(close, timeperiod=period)

        # Moving Average Convergence Divergence (MACD) for different periods
        if len(candles) >= 26:  # MACD needs minimum 26 periods (slowperiod + signalperiod)
            indicators['macd_7'], indicators['macdsignal_7'], indicators['macdhist_7'] = (
                stream.MACD(close, fastperiod=7, slowperiod=14, signalperiod=9)
            )

        # On-Balance Volume (OBV)
        indicators['obv'] = stream.OBV(close, volume)

        # Handle NaN/infinite values
        for key, value in indicators.items():
            if np.isnan(value) or np.isinf(value):
                logger.debug(f"Removing invalid indicator {key}: {value}")
                indicators[key] = None

    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")
        return {**candle}


    return {
        **candle,
        **indicators,
    }

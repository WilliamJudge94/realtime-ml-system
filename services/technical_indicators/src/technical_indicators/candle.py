from typing import Dict, Optional
from quixstreams import State

from config.config import load_settings, Settings


def are_same_window(candle: Dict, previous_candle: Dict) -> bool:
    """
    Returns True if the two candles correspond to the same time window and crypto currency
    """
    return (
        candle['pair'] == previous_candle['pair']
        and candle['window_start_ms'] == previous_candle['window_start_ms']
        and candle['window_end_ms'] == previous_candle['window_end_ms']
    )


def update_candles_in_state(candle: Dict, state: State, settings: Optional[Settings] = None) -> Dict:
    """
    Takes the current state (with the list of N previous candles) and the latest
    candle, and update this list.

    It can either happen that the latest candle corresponds to the same time window
    as the last candle in the list, or that it corresponds to a new time window.

    Args:
        candle (dict): The latest candle
        state (State): The current state with the list of N previous candles

    Return:
        None
    """
    candles = state.get('candles', default=[])

    # we need to check if the new `candle` corresponds to the same
    # (window_start_ms, window_end_ms) as `candles[-1]`
    if not candles:
        # If there are no candles in the state, add the new candle
        candles.append(candle)
    elif are_same_window(candle, candles[-1]):
        # Replace the latest candle in state
        candles[-1] = candle
    else:
        # Add the new candle to the state
        candles.append(candle)

    # Use provided settings or load if not provided (for backward compatibility)
    if settings is None:
        settings = load_settings()
    if len(candles) > settings.max_candles_in_state:
        # Remove the oldest candle from the state
        candles.pop(0)

    state.set('candles', candles)

    return candle

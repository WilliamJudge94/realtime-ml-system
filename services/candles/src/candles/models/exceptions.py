"""
Simplified exceptions for candle processing.
"""


class CandleError(Exception):
    """Base exception for candle processing errors with optional context."""
    
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
"""
Exceptions for technical indicator processing.
"""


class TechnicalIndicatorError(Exception):
    """Base exception for technical indicator processing errors with optional context."""
    
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class InsufficientDataError(TechnicalIndicatorError):
    """Raised when there's insufficient data to calculate a technical indicator."""
    pass


class InvalidIndicatorParameterError(TechnicalIndicatorError):
    """Raised when invalid parameters are provided for indicator calculation."""
    pass
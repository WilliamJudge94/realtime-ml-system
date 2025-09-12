"""
Prediction service exceptions.
"""


class PredictionError(Exception):
    """Base exception for prediction service."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ModelError(PredictionError):
    """Exception raised when model operations fail."""
    pass


class ValidationError(PredictionError):
    """Exception raised when data validation fails."""
    pass


class InputError(PredictionError):
    """Exception raised when input data is invalid."""
    pass
"""
Essential exceptions for candle processing.

Provides clear error types for trade validation and candle processing
without over-engineering.
"""


class CandleProcessingError(Exception):
    """Base exception for candle processing errors."""
    
    def __init__(self, message: str, context: dict = None):
        """Initialize with message and optional context."""
        super().__init__(message)
        self.message = message
        self.context = context or {}


class InvalidTradeError(CandleProcessingError):
    """Raised when trade data fails validation."""
    
    def __init__(self, message: str, trade_data: dict = None, field: str = None):
        """Initialize with trade validation context."""
        context = {}
        if field:
            context["failed_field"] = field
        if trade_data:
            # Only include safe fields to avoid logging sensitive data
            safe_fields = ["product_id", "timestamp_ms"]
            context["trade_info"] = {
                k: v for k, v in trade_data.items() 
                if k in safe_fields
            }
        
        super().__init__(message, context)
        self.trade_data = trade_data
        self.field = field


class ValidationError(CandleProcessingError):
    """Raised when validation operations fail."""
    
    def __init__(self, message: str, validation_type: str = None):
        """Initialize with validation context."""
        context = {}
        if validation_type:
            context["validation_type"] = validation_type
            
        super().__init__(message, context)
        self.validation_type = validation_type
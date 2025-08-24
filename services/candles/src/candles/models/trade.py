"""
Simple trade validation using pydantic.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from pydantic import BaseModel, field_validator

from .exceptions import CandleError


class Trade(BaseModel):
    """Simple trade data validation without over-engineering."""
    product_id: str
    price: float
    quantity: float
    timestamp_ms: int
    
    @field_validator('product_id')
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        if not v.strip():
            raise CandleError("Product ID cannot be empty", {"field": "product_id"})
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise CandleError(f"Price must be positive: {v}", {"field": "price"})
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v < 0:
            raise CandleError(f"Quantity cannot be negative: {v}", {"field": "quantity"})
        return v
    
    @field_validator('timestamp_ms')
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        # Basic timestamp validation - not too old or in future
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        if v > now_ms + 60000:  # 1 minute future tolerance
            raise CandleError(f"Timestamp in future: {v}", {"field": "timestamp_ms"})
        if v < now_ms - 86400000:  # 24 hour old tolerance
            raise CandleError(f"Timestamp too old: {v}", {"field": "timestamp_ms"})
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create Trade from dictionary with type conversion."""
        try:
            return cls(**data)
        except Exception as e:
            raise CandleError(f"Invalid trade data: {e}", {"trade_data": data}) from e
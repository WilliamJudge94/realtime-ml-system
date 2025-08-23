"""
Simple trade validation using dataclasses.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any

from .exceptions import CandleError


@dataclass
class Trade:
    """Simple trade data validation without over-engineering."""
    product_id: str
    price: float
    quantity: float
    timestamp_ms: int
    
    def __post_init__(self):
        """Basic validation after initialization."""
        if not self.product_id.strip():
            raise CandleError("Product ID cannot be empty", {"field": "product_id"})
        
        if self.price <= 0:
            raise CandleError(f"Price must be positive: {self.price}", {"field": "price"})
        
        if self.quantity < 0:
            raise CandleError(f"Quantity cannot be negative: {self.quantity}", {"field": "quantity"})
        
        # Basic timestamp validation - not too old or in future
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        if self.timestamp_ms > now_ms + 60000:  # 1 minute future tolerance
            raise CandleError(f"Timestamp in future: {self.timestamp_ms}", {"field": "timestamp_ms"})
        if self.timestamp_ms < now_ms - 86400000:  # 24 hour old tolerance
            raise CandleError(f"Timestamp too old: {self.timestamp_ms}", {"field": "timestamp_ms"})
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create Trade from dictionary with type conversion."""
        try:
            return cls(
                product_id=str(data['product_id']),
                price=float(data['price']),
                quantity=float(data['quantity']),
                timestamp_ms=int(data['timestamp_ms'])
            )
        except (KeyError, ValueError, TypeError) as e:
            raise CandleError(f"Invalid trade data: {e}", {"trade_data": data}) from e
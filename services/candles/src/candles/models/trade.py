"""
Lightweight trade message validation for incoming data quality.

Provides essential validation for trade messages without over-engineering.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any

from pydantic import BaseModel, Field, field_validator

from .exceptions import InvalidTradeError


class TradeMessage(BaseModel):
    """
    Validates incoming trade messages for data quality.
    
    Focuses on essential validation to catch obvious data issues
    without being overly restrictive.
    """
    
    # Core fields from previous_main.py
    product_id: str = Field(..., min_length=1, description="Trading pair symbol") 
    price: Decimal = Field(..., gt=0, description="Trade price")
    quantity: Decimal = Field(..., ge=0, description="Trade volume/quantity")
    timestamp_ms: int = Field(..., description="Trade timestamp in milliseconds")
    
    class Config:
        """Pydantic model configuration."""
        extra = "allow"  # Allow additional fields for flexibility
        validate_assignment = True
    
    @field_validator('product_id')
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        """Basic product ID validation."""
        v = v.strip()
        if not v:
            raise InvalidTradeError("Product ID cannot be empty", field="product_id")
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Basic price validation."""
        # Simple bounds check - adjust based on your asset classes
        if v > Decimal('10000000'):  # 10M max price
            raise InvalidTradeError(f"Price too high: {v}", field="price")
        return v
    
    @field_validator('quantity')
    @classmethod  
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Basic quantity validation."""
        if v > Decimal('1000000000'):  # 1B max quantity
            raise InvalidTradeError(f"Quantity too high: {v}", field="quantity") 
        return v
    
    @field_validator('timestamp_ms')
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        """Basic timestamp validation."""
        # Check if timestamp is reasonable (not in far future/past)
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Allow 1 minute in future for clock skew
        if v > now_ms + 60000:
            raise InvalidTradeError(f"Timestamp in future: {v}", field="timestamp_ms")
        
        # Reject very old data (older than 24 hours)
        if v < now_ms - 86400000:
            raise InvalidTradeError(f"Timestamp too old: {v}", field="timestamp_ms")
        
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeMessage':
        """Create TradeMessage from dictionary, handling type conversion."""
        try:
            # Handle string to Decimal conversion
            if 'price' in data and isinstance(data['price'], (str, float)):
                data['price'] = Decimal(str(data['price']))
            if 'quantity' in data and isinstance(data['quantity'], (str, float)):
                data['quantity'] = Decimal(str(data['quantity']))
            
            return cls(**data)
            
        except Exception as e:
            raise InvalidTradeError(f"Failed to parse trade data: {e}", trade_data=data) from e
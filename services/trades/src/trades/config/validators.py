import re
from typing import List


def validate_live_or_historical(cls, v: str) -> str:
    if v.lower() not in {"live", "historical"}:
        raise ValueError("must be 'live' or 'historical'")
    return v.lower()


def validate_product_ids(cls, v: List[str]) -> List[str]:
    if not v:
        raise ValueError("cannot be empty")
    
    pattern = r'^[A-Z0-9]{2,10}[\/\-]?[A-Z0-9]{2,10}$'
    for product_id in v:
        if not re.match(pattern, product_id.upper()):
            raise ValueError(f"'{product_id}' invalid format")
    
    return [pid.upper() for pid in v]
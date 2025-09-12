import re
from typing import List


def validate_processing_mode(cls, v: str) -> str:
    """Validate processing mode is either 'live' or 'historical'"""
    if v.lower() not in {"live", "historical"}:
        raise ValueError("must be 'live' or 'historical'")
    return v.lower()


def validate_trading_pair(cls, v: str) -> str:
    """Validate trading pair format (e.g., BTC/USD, ETH-BTC)"""
    pattern = r'^[A-Z0-9]{2,10}[\/\-]?[A-Z0-9]{2,10}$'
    if not re.match(pattern, v.upper()):
        raise ValueError(f"'{v}' invalid trading pair format")
    return v.upper()


def validate_feature_list(cls, v: List[str]) -> List[str]:
    """Validate feature list is not empty and contains valid feature names"""
    if not v:
        raise ValueError("features list cannot be empty")
    
    # Basic validation for feature names - alphanumeric with underscores
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    for feature in v:
        if not re.match(pattern, feature):
            raise ValueError(f"'{feature}' is not a valid feature name")
    
    return v


def validate_model_name(cls, v: str) -> str:
    """Validate model name format"""
    if not v or len(v) > 100:
        raise ValueError("model_name must be 1-100 characters")
    if not re.match(r'^[a-zA-Z0-9\-\_]+$', v):
        raise ValueError("model_name can only contain alphanumeric, hyphens, underscores")
    return v


def validate_file_path(cls, v: str) -> str:
    """Validate file path format"""
    if not v:
        raise ValueError("file path cannot be empty")
    # Allow relative and absolute paths
    if not re.match(r'^[a-zA-Z0-9\-\_\.\/\\:]+$', v):
        raise ValueError("invalid file path format")
    return v
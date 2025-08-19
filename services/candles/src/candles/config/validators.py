import re
from typing import Any
from pydantic import field_validator, ValidationInfo


def validate_candle_interval(cls, v: int) -> int:
    """Validate candle interval is within acceptable range (1 second to 1 day)."""
    if not isinstance(v, int):
        raise ValueError("candle_seconds must be an integer")
    if v < 1:
        raise ValueError("candle_seconds must be at least 1 second")
    if v > 86400:  # 24 hours * 60 minutes * 60 seconds
        raise ValueError("candle_seconds cannot exceed 86400 seconds (1 day)")
    return v


def validate_kafka_broker(cls, v: str) -> str:
    """Validate Kafka broker address format (host:port)."""
    if not isinstance(v, str):
        raise ValueError("kafka_broker_address must be a string")
    
    # Basic host:port pattern validation
    pattern = r'^[a-zA-Z0-9\-\.]+:\d+$'
    if not re.match(pattern, v):
        raise ValueError(
            "kafka_broker_address must be in format 'host:port' "
            "(e.g., 'localhost:9092' or 'kafka-server:9092')"
        )
    
    # Extract and validate port
    host, port_str = v.rsplit(':', 1)
    try:
        port = int(port_str)
        if port < 1 or port > 65535:
            raise ValueError("port must be between 1 and 65535")
    except ValueError as e:
        if "port must be between" in str(e):
            raise e
        raise ValueError("port must be a valid integer")
    
    return v


def validate_log_level(cls, v: str) -> str:
    """Validate log level is one of the accepted values."""
    if not isinstance(v, str):
        raise ValueError("log_level must be a string")
    
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    v_upper = v.upper()
    
    if v_upper not in valid_levels:
        raise ValueError(
            f"log_level must be one of: {', '.join(sorted(valid_levels))}. "
            f"Got: {v}"
        )
    
    return v_upper


def validate_positive_int(cls, v: int) -> int:
    """Validate that an integer is positive."""
    if not isinstance(v, int):
        raise ValueError("value must be an integer")
    if v <= 0:
        raise ValueError("value must be positive (greater than 0)")
    return v


def validate_topic_name(cls, v: str) -> str:
    """Validate Kafka topic name follows naming conventions."""
    if not isinstance(v, str):
        raise ValueError("topic name must be a string")
    
    if not v:
        raise ValueError("topic name cannot be empty")
    
    if len(v) > 255:
        raise ValueError("topic name cannot exceed 255 characters")
    
    # Kafka topic naming rules: alphanumeric, hyphens, underscores, dots
    pattern = r'^[a-zA-Z0-9\-\_\.]+$'
    if not re.match(pattern, v):
        raise ValueError(
            "topic name can only contain alphanumeric characters, "
            "hyphens (-), underscores (_), and dots (.)"
        )
    
    # Additional restrictions
    if v.startswith('.') or v.startswith('_'):
        raise ValueError("topic name cannot start with '.' or '_'")
    
    return v


def validate_consumer_group(cls, v: str) -> str:
    """Validate Kafka consumer group name."""
    if not isinstance(v, str):
        raise ValueError("consumer group must be a string")
    
    if not v:
        raise ValueError("consumer group cannot be empty")
    
    if len(v) > 255:
        raise ValueError("consumer group name cannot exceed 255 characters")
    
    # Similar rules to topic names but more restrictive
    pattern = r'^[a-zA-Z0-9\-\_]+$'
    if not re.match(pattern, v):
        raise ValueError(
            "consumer group name can only contain alphanumeric characters, "
            "hyphens (-), and underscores (_)"
        )
    
    return v


def validate_app_name(cls, v: str) -> str:
    """Validate application name."""
    if not isinstance(v, str):
        raise ValueError("app_name must be a string")
    
    if not v:
        raise ValueError("app_name cannot be empty")
    
    if len(v) > 100:
        raise ValueError("app_name cannot exceed 100 characters")
    
    # Allow alphanumeric, hyphens, underscores
    pattern = r'^[a-zA-Z0-9\-\_]+$'
    if not re.match(pattern, v):
        raise ValueError(
            "app_name can only contain alphanumeric characters, "
            "hyphens (-), and underscores (_)"
        )
    
    return v
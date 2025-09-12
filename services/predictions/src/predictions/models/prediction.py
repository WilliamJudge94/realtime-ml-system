"""
Prediction model using pydantic.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from .exceptions import PredictionError, ValidationError


class Prediction(BaseModel):
    """Prediction data structure with validation."""
    pair: str
    prediction_timestamp_ms: int
    prediction_value: float
    confidence_score: float
    model_name: str
    model_version: str
    prediction_horizon_minutes: int
    features_used: List[str]
    input_indicators: Dict[str, Any]
    schema_version: str = "1.0"
    
    # Optional metadata
    signal_strength: Optional[float] = None
    prediction_type: str = "price_direction"  # price_direction, price_value, volatility, etc.
    
    @field_validator('prediction_value')
    @classmethod
    def validate_prediction_value(cls, v: float) -> float:
        if v <= 0:
            raise ValidationError(f"Prediction value must be positive: {v}")
        return v
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValidationError(f"Confidence score must be between 0 and 1: {v}")
        return v
    
    @field_validator('signal_strength')
    @classmethod
    def validate_signal_strength(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not -1.0 <= v <= 1.0:
            raise ValidationError(f"Signal strength must be between -1 and 1: {v}")
        return v
    
    @field_validator('prediction_horizon_minutes')
    @classmethod
    def validate_prediction_horizon(cls, v: int) -> int:
        if v <= 0:
            raise ValidationError("Prediction horizon must be positive")
        return v
    
    @field_validator('features_used')
    @classmethod
    def validate_features_used(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValidationError("Features used cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_model_consistency(self) -> 'Prediction':
        """Validate model consistency and business rules."""
        
        # Ensure model name and version are not empty
        if not self.model_name.strip():
            raise ValidationError("Model name cannot be empty")
        if not self.model_version.strip():
            raise ValidationError("Model version cannot be empty")
        
        # Validate prediction timestamp is reasonable (not too far in future/past)
        current_timestamp_ms = int(datetime.now().timestamp() * 1000)
        time_diff_hours = abs(self.prediction_timestamp_ms - current_timestamp_ms) / (1000 * 60 * 60)
        
        if time_diff_hours > 24:
            raise ValidationError(f"Prediction timestamp seems unreasonable: {time_diff_hours} hours from current time")
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Kafka output."""
        data = self.model_dump()
        # Convert float values to strings for consistency with other services
        for field in ['prediction_value', 'confidence_score']:
            if field in data and data[field] is not None:
                data[field] = str(data[field])
        if data.get('signal_strength') is not None:
            data['signal_strength'] = str(data['signal_strength'])
        return data
    
    @classmethod
    def from_indicators(cls, indicators: Dict[str, Any], model_output: Dict[str, Any]) -> 'Prediction':
        """Create Prediction from technical indicators and model output."""
        try:
            return cls(
                pair=indicators['pair'],
                prediction_timestamp_ms=int(datetime.now().timestamp() * 1000),
                prediction_value=model_output['prediction_value'],
                confidence_score=model_output['confidence_score'],
                model_name=model_output['model_name'],
                model_version=model_output['model_version'],
                prediction_horizon_minutes=model_output['prediction_horizon_minutes'],
                features_used=model_output['features_used'],
                input_indicators=indicators,
                signal_strength=model_output.get('signal_strength'),
                prediction_type=model_output.get('prediction_type', 'price_direction')
            )
        except Exception as e:
            raise PredictionError(f"Failed to create prediction: {e}") from e
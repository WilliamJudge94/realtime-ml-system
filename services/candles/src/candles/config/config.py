import os
from pathlib import Path
from typing import Optional, Any
from loguru import logger
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from .validators import (
    validate_candle_interval,
    validate_kafka_broker,
    validate_log_level,
    validate_topic_name,
    validate_consumer_group,
    validate_app_name,
)


class ConfigurationError(Exception):
    """Raised when configuration loading fails."""
    pass


class ConfigurationLoader:
    """Handles loading and validation of configuration from multiple sources."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files. 
                       Defaults to the directory containing this file.
        """
        self.config_dir = config_dir or Path(__file__).parent
    
    def get_environment(self) -> str:
        """Get the current environment, with fallback to development."""
        env = os.getenv('ENV')
        if env is None:
            logger.warning("ENV environment variable not set, using default 'development' configuration")
            return 'development'
        return env
    
    def get_env_file_path(self, environment: str) -> Path:
        """Get the path to the environment file for the given environment."""
        return self.config_dir / f".env.{environment}"
    
    def validate_env_file(self, env_file_path: Path) -> None:
        """Validate that the environment file exists and is readable.
        
        Args:
            env_file_path: Path to the environment file
            
        Raises:
            ConfigurationError: If the file doesn't exist or isn't readable
        """
        if not env_file_path.exists():
            raise ConfigurationError(f"Environment file not found: {env_file_path}")
        
        if not env_file_path.is_file():
            raise ConfigurationError(f"Environment path is not a file: {env_file_path}")
        
        try:
            env_file_path.read_text()
        except PermissionError:
            raise ConfigurationError(f"Cannot read environment file: {env_file_path}")
    
    def create_settings_config(self, environment: str) -> SettingsConfigDict:
        """Create the Pydantic settings configuration.
        
        Args:
            environment: The environment name
            
        Returns:
            Configured SettingsConfigDict
            
        Raises:
            ConfigurationError: If environment file validation fails
        """
        env_file_path = self.get_env_file_path(environment)
        self.validate_env_file(env_file_path)
        
        logger.debug(f"Loading settings from {env_file_path}")
        
        return SettingsConfigDict(
            env_file=str(env_file_path),
            env_file_encoding="utf-8",
            env_prefix="CANDLES_",
            case_sensitive=False,
            extra="forbid",
        )


class BaseConfig(BaseSettings):
    """Base configuration class with common settings and validation."""
    
    # Application settings
    app_name: str = "candles"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # Kafka settings
    kafka_broker_address: str = "localhost:9092"
    kafka_input_topic: str = "trades"
    kafka_output_topic: str = "candles"
    kafka_consumer_group: str = "candles_consumer_group"

    # Candle processing settings
    candle_seconds: int = 60

    # Field validators
    @field_validator('app_name')
    @classmethod
    def validate_app_name_field(cls, v: str) -> str:
        return validate_app_name(cls, v)

    @field_validator('log_level')
    @classmethod
    def validate_log_level_field(cls, v: str) -> str:
        return validate_log_level(cls, v)

    @field_validator('kafka_broker_address')
    @classmethod
    def validate_kafka_broker_field(cls, v: str) -> str:
        return validate_kafka_broker(cls, v)

    @field_validator('kafka_input_topic', 'kafka_output_topic')
    @classmethod
    def validate_topic_name_field(cls, v: str) -> str:
        return validate_topic_name(cls, v)

    @field_validator('kafka_consumer_group')
    @classmethod
    def validate_consumer_group_field(cls, v: str) -> str:
        return validate_consumer_group(cls, v)

    @field_validator('candle_seconds')
    @classmethod
    def validate_candle_interval_field(cls, v: int) -> int:
        return validate_candle_interval(cls, v)

    @model_validator(mode='after')
    def validate_cross_field_constraints(self) -> 'BaseConfig':
        """Validate cross-field business rules."""
        # Ensure consumer groups are unique across environments
        # This is a basic check - in production you might want to check against a registry
        
        # Validate log format
        if self.log_format not in ['json', 'text']:
            raise ValueError("log_format must be either 'json' or 'text'")
        
        # Business rule: production environments should use WARNING or higher log level
        if 'prod' in self.app_name.lower() and self.log_level in ['DEBUG', 'INFO']:
            logger.warning(
                f"Production app '{self.app_name}' using log level '{self.log_level}'. "
                "Consider using WARNING or ERROR for production."
            )
        
        return self

    def log_configuration_summary(self) -> None:
        """Log a summary of the loaded configuration."""
        logger.info(f"Configuration loaded for app: {self.app_name}")
        logger.info(f"Environment: {'development' if self.debug else 'production-like'}")
        logger.info(f"Log level: {self.log_level}")
        logger.info(f"Kafka broker: {self.kafka_broker_address}")
        logger.info(f"Input topic: {self.kafka_input_topic}")
        logger.info(f"Output topic: {self.kafka_output_topic}")
        logger.info(f"Consumer group: {self.kafka_consumer_group}")
        logger.info(f"Candle interval: {self.candle_seconds} seconds")


class Settings(BaseConfig):
    """Configuration settings with inheritance from BaseConfig."""
    pass


def load_settings(environment: Optional[str] = None, config_dir: Optional[Path] = None) -> Settings:
    """Load configuration settings with proper error handling.
    
    Args:
        environment: Environment name. If None, will be determined from ENV variable.
        config_dir: Directory containing configuration files. 
                   Defaults to the directory containing this file.
    
    Returns:
        Configured Settings instance
        
    Raises:
        ConfigurationError: If configuration loading fails
    """
    try:
        loader = ConfigurationLoader(config_dir)
        
        if environment is None:
            environment = loader.get_environment()
        
        settings_config = loader.create_settings_config(environment)
        
        # Create settings class with dynamic configuration
        class ConfiguredSettings(Settings):
            model_config = settings_config
        
        settings = ConfiguredSettings()
        
        # Log configuration summary
        settings.log_configuration_summary()
        
        return settings
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Failed to load configuration: {e}") from e

import os
from pathlib import Path
from typing import Optional
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class Settings(BaseSettings):
    """Pure configuration data class with validation."""
    
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
        
        return ConfiguredSettings()
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Failed to load configuration: {e}") from e

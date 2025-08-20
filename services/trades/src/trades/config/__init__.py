from .config import Settings, load_settings

config = load_settings()

__all__ = ['config', 'Settings', 'load_settings']
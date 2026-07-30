"""Settings loading utility with support for default fallbacks and custom overrides."""

from pathlib import Path
from loguru import logger
from discordbuddy.config.settings import Settings


def load_settings(config_file: str | Path | None = None) -> Settings:
    """Load settings from environment variables, optional .env file, or defaults.

    Args:
        config_file: Optional path to a specific configuration file.

    Returns:
        Settings: Instantiated application configuration object.
    """
    logger.debug("Loading DiscordBuddy configuration settings...")
    try:
        settings = Settings()
        logger.info(f"Loaded configuration for environment: '{settings.environment}'")
        return settings
    except Exception as exc:
        logger.error(f"Failed to load configuration: {exc}")
        raise exc

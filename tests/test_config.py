"""Unit tests for configuration loading and validation."""

from discordbuddy.config.loader import load_settings
from discordbuddy.config.settings import Settings


def test_load_default_settings() -> None:
    """Test loading default configuration settings."""
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "DiscordBuddy"
    assert settings.hardware.gpu_name == "AMD Radeon RX 6700 XT 12GB"
    assert settings.brain.backend_type == "openai_api"
    assert settings.brain.api_base_url == "http://127.0.0.1:1234/v1"
    assert settings.brain.model_name == "qwen3-14b-instruct"
    assert settings.vision.capture_fps == 2


def test_custom_setting_values(test_settings: Settings) -> None:
    """Test custom setting overrides."""
    assert test_settings.environment == "testing"
    assert test_settings.log_level == "DEBUG"

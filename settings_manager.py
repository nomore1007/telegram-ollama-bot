"""
Settings management for the Deepthought Bot.

Handles loading of user settings and fallback to example settings.
"""

import os
import sys
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages loading and validation of bot settings."""

    def __init__(self):
        # Determine the base directory for config files
        # Prioritize BOT_CONFIG_DIR environment variable, otherwise use current file's directory
        self._config_dir = Path(os.getenv("BOT_CONFIG_DIR", Path(__file__).parent))
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Load settings with proper fallback logic."""
        # Priority order: settings.example.py -> settings.py -> environment variables

        # 1. Load example settings for defaults
        example_settings_file = self._config_dir / 'settings.example.py'
        if example_settings_file.exists():
            try:
                self._load_settings_file(example_settings_file, is_example=True)
                logger.info(f"Loaded default settings from: {example_settings_file}")
            except Exception as e:
                logger.error(f"Error loading {example_settings_file}: {e}")
        else:
            raise FileNotFoundError(f"{example_settings_file} not found. This file is required for default settings.")

        # 2. Load user settings to override defaults
        user_settings_file = self._config_dir / 'settings.py'
        if user_settings_file.exists():
            try:
                self._load_settings_file(user_settings_file)
                logger.info(f"Loaded user settings from: {user_settings_file}")
            except Exception as e:
                logger.error(f"Error loading {user_settings_file}: {e}")
        else:
            logger.warning("No settings.py file found. Using default settings. Please create one from settings.example.py for your configuration.")

        # 3. Apply environment variables as final overrides
        self._load_environment_variables()

        # 4. Validate required settings
        self._validate_required_settings()

    def _load_settings_file(self, settings_file: Path, is_example: bool = False):
        """Load settings from a Python file safely."""
        if is_example:
            self.settings = {} # Always start fresh with defaults

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        globals_dict = {}
        locals_dict = {}

        try:
            exec(content, globals(), locals_dict)

            for key, value in locals_dict.items():
                if key.isupper():
                    self.settings[key] = value

        except Exception as e:
            logger.error(f"Error loading settings from {settings_file}: {e}")
            raise

    def _load_environment_variables(self):
        """Load settings from environment variables, overriding existing settings."""
        for key, value in os.environ.items():
            if key.isupper() and key.startswith(('TELEGRAM_', 'DISCORD_', 'OLLAMA_', 'OPENAI_', 'GROQ_', 'TOGETHER_', 'HUGGINGFACE_', 'ANTHROPIC_', 'DEFAULT_', 'MAX_', 'LOG_', 'ADMIN_', 'DATABASE_', 'OPENWEATHERMAP_', 'PLUGINS_')):
                # Attempt to convert to appropriate type if possible
                if value.lower() == 'true':
                    self.settings[key] = True
                elif value.lower() == 'false':
                    self.settings[key] = False
                elif value.isdigit():
                    self.settings[key] = int(value)
                elif re.match(r'^\d+\.\d+$', value):
                    self.settings[key] = float(value)
                elif key == 'ADMIN_USER_IDS': # Special case for list of integers
                    try:
                        self.settings[key] = [int(uid.strip()) for uid in value.split(',')]
                    except ValueError:
                        logger.warning(f"Invalid ADMIN_USER_IDS environment variable: {value}. Must be comma-separated integers.")
                        self.settings[key] = []
                elif key == 'ENABLED_PLUGINS': # Special case for comma-separated plugins
                    self.settings[key] = [p.strip() for p in value.split(',')]
                else:
                    self.settings[key] = value
                logger.debug(f"Overridden setting from environment: {key}={self.settings[key]}")

    def _validate_required_settings(self):
        """Validate that required settings are present."""
        missing = []

        # Check for Telegram bot token
        enabled_plugins = self.settings.get('ENABLED_PLUGINS', [])
        if 'telegram' in enabled_plugins:
            # Check new per-plugin format first
            plugins = self.settings.get('PLUGINS', {})
            if plugins:
                telegram_config = plugins.get('telegram', {})
                bot_token = telegram_config.get('bot_token')
                if not bot_token or (isinstance(bot_token, str) and bot_token.startswith('YOUR_') and bot_token.endswith('_HERE')):
                    missing.append('TELEGRAM_BOT_TOKEN (in PLUGINS["telegram"]["bot_token"])')
            else:
                # Fallback to old global format for backward compatibility
                bot_token = self.settings.get('TELEGRAM_BOT_TOKEN')
                if not bot_token or (isinstance(bot_token, str) and bot_token.startswith('YOUR_') and bot_token.endswith('_HERE')):
                    missing.append('TELEGRAM_BOT_TOKEN')

        # Check for Ollama host (still global)
        ollama_host = self.settings.get('OLLAMA_HOST')
        if not ollama_host:
            missing.append('OLLAMA_HOST')

        if missing:
            raise ValueError(
                f"Required settings are missing or not configured: {', '.join(missing)}. "
                f"Please check your settings.py file and replace placeholder values with actual configuration."
            )

    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)

    def __getitem__(self, key: str):
        """Allow dictionary-style access."""
        return self.settings[key]

    def __contains__(self, key: str):
        """Check if a setting exists."""
        return key in self.settings

    def __getattr__(self, name: str):
        """Allow attribute-style access."""
        try:
            return self.settings[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' has no setting '{name}'")


# Create global settings instance
settings_manager = SettingsManager()

# For backward compatibility, create a settings object
class Config:
    """Backward compatibility wrapper."""
    def __getattr__(self, name):
        if name == "BOT_CONFIG_DIR":
            return settings_manager._config_dir
        return settings_manager.get(name)

    def __getitem__(self, name):
        if name == "BOT_CONFIG_DIR":
            return settings_manager._config_dir
        return settings_manager[name]

    def __contains__(self, name):
        if name == "BOT_CONFIG_DIR":
            return True # Always consider BOT_CONFIG_DIR as contained
        return name in settings_manager

    def get(self, key, default=None):
        """Get a setting value with default."""
        if key == "BOT_CONFIG_DIR":
            return settings_manager._config_dir
        return settings_manager.get(key, default)

# Create backward-compatible settings object
settings = Config()
config = settings
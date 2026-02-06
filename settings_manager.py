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
import shutil # For copying the example config

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages loading and validation of bot settings."""

    def __init__(self):
        # Determine the base directory for persistent config files (user-editable)
        # Prioritize BOT_CONFIG_DIR environment variable, otherwise use current working directory
        self._config_dir = Path(os.getenv("BOT_CONFIG_DIR", Path.cwd()))

        # Determine the application source directory (where config.example.py is)
        # In Docker, this is /app. Outside Docker, it's the script's directory.
        self._app_source_dir = Path(os.getenv("BOT_APP_SOURCE_DIR", Path(__file__).parent))

        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Load settings with proper fallback logic."""
        # Priority order: config.py (user) -> config.example.py (fallback) -> environment variables

        # Define config file paths
        example_config_file = self._app_source_dir / 'config.example.py'
        user_config_file = self._config_dir / 'config.py'

        if not example_config_file.exists():
            raise FileNotFoundError(f"{example_config_file} not found. This template file is required for default settings.")

        # Attempt to load user config file
        if user_config_file.exists():
            try:
                self._load_config_file(user_config_file)
                logger.info(f"Loaded configuration from: {user_config_file}")
            except Exception as e:
                logger.error(f"Error loading user config file '{user_config_file}': {e}. Falling back to example defaults.")
                # If user config is broken, try loading example defaults
                self._load_config_file(example_config_file, is_example=True)
        else:
            # If user config file doesn't exist, load example defaults directly
            self._load_config_file(example_config_file, is_example=True)
            logger.warning(f"Configuration file '{user_config_file.name}' not found. Using defaults from '{example_config_file.name}'.")


        # Apply environment variables as final overrides
        self._load_environment_variables()

        # Validate required settings
        self._validate_required_settings()

    def _load_config_file(self, config_file: Path, is_example: bool = False):
        """Load settings from a Python config file safely."""
        if is_example:
            # Clear settings if loading example to ensure a clean slate for defaults
            self.settings = {}

        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        globals_dict = {}
        locals_dict = {}

        try:
            exec(content, globals(), locals_dict)

            for key, value in locals_dict.items():
                if key.isupper(): # Conventionally, settings are uppercase
                    self.settings[key] = value

        except Exception as e:
            logger.error(f"Error loading settings from {config_file}: {e}")
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
                # Handle specific plugin tokens that need nested structure
                elif key == 'TELEGRAM_BOT_TOKEN':
                    if 'PLUGINS' not in self.settings:
                        self.settings['PLUGINS'] = {}
                    if 'telegram' not in self.settings['PLUGINS']:
                        self.settings['PLUGINS']['telegram'] = {}
                    self.settings['PLUGINS']['telegram']['bot_token'] = value
                    logger.debug(f"Overridden setting from environment: PLUGINS['telegram']['bot_token']={self.settings['PLUGINS']['telegram']['bot_token']}")
                elif key == 'DISCORD_BOT_TOKEN':
                    if 'PLUGINS' not in self.settings:
                        self.settings['PLUGINS'] = {}
                    if 'discord' not in self.settings['PLUGINS']:
                        self.settings['PLUGINS']['discord'] = {}
                    self.settings['PLUGINS']['discord']['bot_token'] = value
                    logger.debug(f"Overridden setting from environment: PLUGINS['discord']['bot_token']={self.settings['PLUGINS']['discord']['bot_token']}")
                else: # Generic handling for other keys
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
                f"Please check your config.py file and replace placeholder values with actual configuration."
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
"""
Settings management for the Deepthought Bot.

Handles loading of user settings and fallback to example settings.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages loading and validation of bot settings."""

    def __init__(self):
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Load settings with proper fallback logic."""
        # Priority order: settings.py (user) -> settings.example.py (fallback)
        settings_files = [
            Path(__file__).parent / 'settings.py',  # User settings (ignored by git)
            Path(__file__).parent / 'settings.example.py',  # Example settings (committed)
        ]

        settings_loaded = False
        loaded_file = None

        for settings_file in settings_files:
            if settings_file.exists():
                try:
                    # Use import-style loading instead of exec for security
                    self._load_settings_file(settings_file)
                    settings_loaded = True
                    loaded_file = settings_file
                    logger.info(f"Loaded settings from: {settings_file}")

                    # If we loaded user settings, we're done
                    if settings_file.name == 'settings.py':
                        break

                except Exception as e:
                    logger.error(f"Error loading {settings_file}: {e}")
                    continue

        if not settings_loaded:
            raise FileNotFoundError(
                "No settings file found. Please create 'settings.py' from 'settings.example.py'"
            )

        # Warn if using example settings
        if loaded_file and loaded_file.name == 'settings.example.py':
            logger.warning(
                "Using example settings. Please copy settings.example.py to settings.py "
                "and configure your actual values (API keys, tokens, etc.)"
            )

        # Validate required settings
        self._validate_required_settings()

    def _load_settings_file(self, settings_file: Path):
        """Load settings from a Python file safely."""
        # For security, we'll use a more controlled approach
        # Read the file and parse it manually instead of using exec

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple parsing - this is safer than exec()
        # We'll look for variable assignments like: VARIABLE_NAME = value

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('"""') or line.startswith("'''"):
                continue

            # Look for variable assignments
            if '=' in line and not line.startswith(' ') and not line.startswith('\t'):
                try:
                    # Split on first = only
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].split(':')[0].strip()
                        var_value_str = parts[1].strip()

                        # Skip if it looks like a complex expression or function call
                        if any(char in var_value_str for char in ['(', ')', 'lambda', 'def', 'class']):
                            continue

                        # Try to evaluate the value safely
                        try:
                            # Create a safe evaluation environment
                            safe_dict = {
                                'os': os,
                                'True': True,
                                'False': False,
                                'None': None,
                                'int': int,
                                'str': str,
                                'float': float,
                                'bool': bool,
                                'list': list,
                                'dict': dict,
                            }

                            var_value = eval(var_value_str, {"__builtins__": {}}, safe_dict)
                            self.settings[var_name] = var_value

                        except (ValueError, SyntaxError, NameError):
                            # If we can't evaluate it safely, store as string
                            # Remove quotes if present
                            if (var_value_str.startswith('"') and var_value_str.endswith('"')) or \
                               (var_value_str.startswith("'") and var_value_str.endswith("'")):
                                var_value_str = var_value_str[1:-1]
                            self.settings[var_name] = var_value_str

                except Exception as e:
                    logger.warning(f"Could not parse line '{line}': {e}")
                    continue

    def _validate_required_settings(self):
        """Validate that required settings are present."""
        required_settings = ['TELEGRAM_BOT_TOKEN']

        missing = []
        for setting in required_settings:
            value = self.settings.get(setting)
            if value is None or (isinstance(value, str) and value.startswith('YOUR_') and value.endswith('_HERE')):
                missing.append(setting)

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
        return settings_manager.get(name)

    def __getitem__(self, name):
        return settings_manager[name]

    def __contains__(self, name):
        return name in settings_manager

# Create backward-compatible settings object
settings = Config()
config = settings
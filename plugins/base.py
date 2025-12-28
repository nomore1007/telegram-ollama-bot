"""
Base plugin system for the Telegram Ollama Bot.

Plugins can extend the bot's functionality by hooking into various events.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from telegram import Update
from telegram.ext import ContextTypes


class Plugin(ABC):
    """
    Abstract base class for all plugins.

    Plugins should implement the methods they need to hook into bot functionality.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def initialize(self, bot_instance) -> None:
        """
        Called when the plugin is loaded. Use this to set up any necessary state.
        """
        pass

    def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance) -> Optional[str]:
        """
        Called for every message. Return a response string to send, or None to ignore.
        """
        return None

    def on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, bot_instance) -> Optional[str]:
        """
        Called for bot commands. Return a response string to send, or None to ignore.
        """
        return None

    def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str, bot_instance) -> Optional[str]:
        """
        Called for callback queries. Return a response string to send, or None to ignore.
        """
        return None

    def get_commands(self) -> List[str]:
        """
        Return a list of command names this plugin handles (without the / prefix).
        """
        return []

    def get_help_text(self) -> str:
        """
        Return help text for this plugin's commands.
        """
        return ""

    def shutdown(self) -> None:
        """
        Called when the bot is shutting down. Clean up resources here.
        """
        pass
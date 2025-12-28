"""
Plugin loading and management system.
"""

import importlib
import inspect
from typing import Dict, List, Type, Optional, Any
from .base import Plugin


class PluginManager:
    """
    Manages loading and initialization of plugins.
    """

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.enabled_plugins: List[str] = []

    def load_plugin(self, plugin_name: str, plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None) -> None:
        """
        Load a plugin by name and class.
        """
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin {plugin_name} already loaded")

        plugin_instance = plugin_class(plugin_name, config)
        self.plugins[plugin_name] = plugin_instance

    def enable_plugin(self, plugin_name: str) -> None:
        """
        Enable a plugin.
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not loaded")
        if plugin_name not in self.enabled_plugins:
            self.enabled_plugins.append(plugin_name)

    def disable_plugin(self, plugin_name: str) -> None:
        """
        Disable a plugin.
        """
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_name)

    def get_enabled_plugins(self) -> List[Plugin]:
        """
        Get all enabled plugin instances.
        """
        return [self.plugins[name] for name in self.enabled_plugins if name in self.plugins]

    def initialize_plugins(self, bot_instance) -> None:
        """
        Initialize all enabled plugins.
        """
        for plugin in self.get_enabled_plugins():
            plugin.initialize(bot_instance)


# Global plugin manager instance
plugin_manager = PluginManager()
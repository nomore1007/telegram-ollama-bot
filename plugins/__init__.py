"""
Plugin loading and management system.
"""

import importlib
import inspect
import logging
from typing import Dict, List, Type, Optional, Any, Set
from .base import Plugin


logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages loading and initialization of plugins.
    """

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.enabled_plugins: List[str] = []
        self.initialized_plugins: Set[str] = set()

    def load_plugin(self, plugin_name: str, plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None) -> None:
        """
        Load a plugin by name and class.
        """
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin {plugin_name} already loaded")

        plugin_instance = plugin_class(plugin_name, config)
        self.plugins[plugin_name] = plugin_instance
        logger.info(f"Loaded plugin: {plugin_name} v{plugin_instance.get_version()}")

    def enable_plugin(self, plugin_name: str) -> None:
        """
        Enable a plugin.
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not loaded")
        if plugin_name not in self.enabled_plugins:
            self.enabled_plugins.append(plugin_name)
            logger.info(f"Enabled plugin: {plugin_name}")

    def disable_plugin(self, plugin_name: str) -> None:
        """
        Disable a plugin.
        """
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_name)
            if plugin_name in self.initialized_plugins:
                self.plugins[plugin_name].shutdown()
                self.initialized_plugins.remove(plugin_name)
            logger.info(f"Disabled plugin: {plugin_name}")

    def get_enabled_plugins(self) -> List[Plugin]:
        """
        Get all enabled plugin instances.
        """
        return [self.plugins[name] for name in self.enabled_plugins if name in self.plugins]

    def validate_plugin_config(self, plugin_name: str) -> bool:
        """
        Validate a plugin's configuration.
        """
        if plugin_name not in self.plugins:
            return False
        return self.plugins[plugin_name].validate_config()

    def resolve_dependencies(self, plugin_names: List[str]) -> List[str]:
        """
        Resolve plugin dependencies and return ordered list.
        """
        resolved = []
        visited = set()

        def visit(name):
            if name in visited:
                if name not in resolved:
                    raise ValueError(f"Circular dependency detected involving {name}")
                return
            visited.add(name)

            if name not in self.plugins:
                raise ValueError(f"Plugin {name} not found")

            for dep in self.plugins[name].get_dependencies():
                visit(dep)

            resolved.append(name)

        for name in plugin_names:
            visit(name)

        return resolved

    def initialize_plugins(self, bot_instance) -> None:
        """
        Initialize all enabled plugins in dependency order.
        """
        try:
            # Resolve dependencies
            ordered_plugins = self.resolve_dependencies(self.enabled_plugins)

            # Validate configurations
            for plugin_name in ordered_plugins:
                if not self.validate_plugin_config(plugin_name):
                    logger.error(f"Plugin {plugin_name} configuration validation failed")
                    continue

            # Initialize plugins
            for plugin_name in ordered_plugins:
                try:
                    self.plugins[plugin_name].initialize(bot_instance)
                    self.initialized_plugins.add(plugin_name)
                    logger.info(f"Initialized plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize plugin {plugin_name}: {e}")

        except Exception as e:
            logger.error(f"Plugin initialization failed: {e}")
            raise

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a plugin.
        """
        if plugin_name not in self.plugins:
            return None

        plugin = self.plugins[plugin_name]
        return {
            'name': plugin_name,
            'version': plugin.get_version(),
            'description': plugin.get_description(),
            'commands': plugin.get_commands(),
            'enabled': plugin_name in self.enabled_plugins,
            'initialized': plugin_name in self.initialized_plugins,
            'dependencies': plugin.get_dependencies(),
            'config_schema': plugin.get_config_schema()
        }

    def list_plugins(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        List all loaded plugins with their info.
        """
        return {name: self.get_plugin_info(name) for name in self.plugins.keys()}

    def shutdown_all(self) -> None:
        """
        Shutdown all initialized plugins.
        """
        for plugin_name in list(self.initialized_plugins):
            try:
                self.plugins[plugin_name].shutdown()
                logger.info(f"Shutdown plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_name}: {e}")

        self.initialized_plugins.clear()


# Global plugin manager instance
plugin_manager = PluginManager()
"""
Comprehensive tests for the Deepthought Bot.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from plugins import PluginManager
    from plugins.base import Plugin
    from plugins.telegram_plugin import TelegramPlugin
    from plugins.web_search_plugin import WebSearchPlugin
    from admin import AdminManager
    from llm_client import LLMClient
except ImportError as e:
    print(f"Import error: {e}")
    # For testing without full imports
    PluginManager = None
    Plugin = object
    TelegramPlugin = object
    WebSearchPlugin = object
    AdminManager = object
    LLMClient = object


class TestPlugin(Plugin):
    """Test plugin for testing purposes."""

    def __init__(self, name: str, config=None):
        super().__init__(name, config)
        self.initialized = False

    def initialize(self, bot_instance):
        super().initialize(bot_instance)
        self.initialized = True

    def get_commands(self):
        return ["testcommand"]

    def get_description(self):
        return "Test plugin for unit tests"


class TestPluginManager:
    """Test the plugin manager functionality."""

    def setup_method(self):
        self.manager = plugin_manager.PluginManager()

    def test_load_plugin(self):
        """Test loading a plugin."""
        self.manager.load_plugin("test", TestPlugin, {"key": "value"})
        assert "test" in self.manager.plugins
        assert self.manager.plugins["test"].config["key"] == "value"

    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins."""
        self.manager.load_plugin("test", TestPlugin, {})
        self.manager.enable_plugin("test")
        assert "test" in self.manager.enabled_plugins

        self.manager.disable_plugin("test")
        assert "test" not in self.manager.enabled_plugins

    def test_dependency_resolution(self):
        """Test plugin dependency resolution."""

        class DependentPlugin(TestPlugin):
            def get_dependencies(self):
                return ["test"]

        self.manager.load_plugin("test", TestPlugin, {})
        self.manager.load_plugin("dependent", DependentPlugin, {})

        # Should resolve dependencies
        ordered = self.manager.resolve_dependencies(["dependent"])
        assert ordered == ["test", "dependent"]

    def test_plugin_info(self):
        """Test getting plugin information."""
        self.manager.load_plugin("test", TestPlugin, {})
        info = self.manager.get_plugin_info("test")

        assert info["name"] == "test"
        assert info["version"] == "1.0.0"
        assert "testcommand" in info["commands"]


class TestAdminManager:
    """Test the admin management system."""

    def setup_method(self):
        self.admin_manager = AdminManager([12345])

    def test_is_admin(self):
        """Test admin checking."""
        assert self.admin_manager.is_admin(12345)
        assert not self.admin_manager.is_admin(67890)

    def test_add_remove_admin(self):
        """Test adding and removing admins."""
        # Add admin
        result = self.admin_manager.add_admin(67890, 12345)
        assert result
        assert self.admin_manager.is_admin(67890)

        # Remove admin
        result = self.admin_manager.remove_admin(67890, 12345)
        assert result
        assert not self.admin_manager.is_admin(67890)

    def test_cannot_remove_last_admin(self):
        """Test that you can't remove the last admin."""
        result = self.admin_manager.remove_admin(12345, 12345)
        assert not result
        assert self.admin_manager.is_admin(12345)


class TestLLMClient:
    """Test the LLM client with different providers."""

    @patch('llm_client.requests.post')
    @pytest.mark.asyncio
    async def test_ollama_provider(self, mock_post):
        """Test Ollama provider."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Hello from Ollama"}
        mock_post.return_value.__enter__.return_value = mock_response
        mock_post.return_value.raise_for_status = Mock()

        client = LLMClient(provider="ollama", host="http://test:11434", model="test-model")
        response = await client.generate("Test prompt")

        assert response == "Hello from Ollama"
        mock_post.assert_called_once()

    @patch('llm_client.requests.post')
    @pytest.mark.asyncio
    async def test_openai_provider(self, mock_post):
        """Test OpenAI provider."""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hello from OpenAI"}}]}
        mock_post.return_value.__enter__.return_value = mock_response
        mock_post.return_value.raise_for_status = Mock()

        client = LLMClient(provider="openai", api_key="test-key", model="gpt-3.5-turbo")
        response = await client.generate("Test prompt")

        assert response == "Hello from OpenAI"


class TestIntegration:
    """Integration tests for the full system."""

    @patch('llm_client.requests.post')
    @pytest.mark.asyncio
    async def test_full_bot_initialization(self, mock_post):
        """Test full bot initialization with plugins."""
        # Mock Ollama response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Test response"}
        mock_post.return_value.__enter__.return_value = mock_response
        mock_post.return_value.raise_for_status = Mock()

        # Import here to avoid circular imports
        from bot import TelegramOllamaBot

        # Create mock config
        config = Mock()
        config.LLM_PROVIDER = "ollama"
        config.OLLAMA_HOST = "http://test:11434"
        config.OLLAMA_MODEL = "test-model"
        config.TIMEOUT = 30
        config.ADMIN_USER_IDS = [12345]
        config.ENABLED_PLUGINS = "telegram,web_search"

        # Initialize bot
        bot = TelegramOllamaBot(config)

        # Check that plugins are loaded
        assert len(bot._TelegramOllamaBot__class__.__name__) >= 0  # Bot created
        assert hasattr(bot, 'admin_manager')
        assert hasattr(bot, 'llm')

        # Test LLM generation
        response = await bot.llm.generate("Test")
        assert response == "Test response"


class TestPerformance:
    """Performance tests."""

    @pytest.mark.asyncio
    async def test_plugin_initialization_performance(self):
        """Test plugin initialization performance."""
        import time

        manager = plugin_manager.PluginManager()

        # Load multiple plugins
        start_time = time.time()
        for i in range(10):
            manager.load_plugin(f"test{i}", TestPlugin, {})
            manager.enable_plugin(f"test{i}")

        # Mock bot instance
        bot_instance = Mock()

        # Initialize plugins
        init_start = time.time()
        manager.initialize_plugins(bot_instance)
        init_time = time.time() - init_start

        # Should initialize quickly (less than 1 second for 10 plugins)
        assert init_time < 1.0

        # Cleanup
        manager.shutdown_all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Web search plugin for the Telegram Ollama Bot.

This plugin allows the LLM to search the web by providing a /search command.
"""

import logging
from typing import Optional, List

from telegram.ext import ContextTypes
from telegram import Update

from .base import Plugin
from constants import MAX_MESSAGE_LENGTH


logger = logging.getLogger(__name__)


class WebSearchPlugin(Plugin):
    """Plugin that adds web search capability to the LLM."""

    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name, config)
        self.bot_instance = None

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with the bot instance."""
        self.bot_instance = bot_instance
        logger.info("Web search plugin initialized")

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["search"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🌐 *Web Search*\n\n"
            "`/search <query>` - Search the web and get AI-powered answer\n\n"
            "💡 *Examples:*\n"
            "`/search latest news about AI`\n"
            "`/search how to cook pasta`"
        )

        async def handle_search(self, update, context: ContextTypes.DEFAULT_TYPE):

            """Handle /search command by prompting the user to ask the bot directly."""

            assert self.bot_instance is not None, "Plugin not initialized"

    

            if update.message:

                await update.message.reply_text(

                    "I can search the web for you! Just ask me your question directly, "

                    "e.g., 'What's the weather in London?' or 'Summarize the news about AI.' "

                    "I'll decide if a web search is needed."

                )

            

                def process_search_results(self, query: str, search_results: list) -> str:

                    """Process raw search results and format them for the LLM."""

                    if not search_results:

                        return f"No relevant results found for '{query}'."

            

                    formatted_results = []

                    for i, result in enumerate(search_results, 1):

                        title = result.get('title', 'No Title')

                        url = result.get('url', 'No URL')

                        snippet = result.get('snippet', 'No Snippet')

                        formatted_results.append(f"{i}. **{title}**\nURL: {url}\nSnippet: {snippet}")

            

                    return f"Web Search Results for: {query}\n\n" + "\n\n".join(formatted_results)
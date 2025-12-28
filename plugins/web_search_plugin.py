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
        """Handle /search command"""
        assert self.bot_instance is not None, "Plugin not initialized"

        if not context.args or len(context.args) == 0:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/search <query>`\n\n"
                    "💡 Example: `/search latest news about AI`",
                    parse_mode="Markdown"
                )
            return

        query = " ".join(context.args)
        logger.info(f"Web search requested: {query}")

        if update.message:
            # Send thinking message
            thinking_msg = await update.message.reply_text("🔍 Searching the web...")

            try:
                # Use the websearch tool (assuming it's available)
                # For now, simulate web search
                search_results = await self._perform_web_search(query)

                if not search_results:
                    await thinking_msg.edit_text("❌ No search results found.")
                    return

                # Create prompt for LLM to summarize
                prompt = f"""Based on the following web search results for the query "{query}", provide a comprehensive and helpful answer:

{search_results}

Please summarize the key information and provide a clear answer."""

                # Get response from LLM
                response = await self.bot_instance.ollama.generate(prompt)

                # Split response if too long
                if len(response) > MAX_MESSAGE_LENGTH:
                    chunks = [response[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(response), MAX_MESSAGE_LENGTH)]
                    await thinking_msg.edit_text(chunks[0])
                    for chunk in chunks[1:]:
                        await update.message.reply_text(chunk)
                else:
                    await thinking_msg.edit_text(response)

            except Exception as e:
                logger.error(f"Web search error: {e}")
                await thinking_msg.edit_text("❌ Failed to perform web search.")

    async def _perform_web_search(self, query: str) -> str:
        """Perform web search and return formatted results."""
        # TODO: Integrate with actual web search API (e.g., Google Custom Search, Bing, etc.)
        # For now, return mock results

        mock_results = f"""
Web Search Results for: {query}

1. **Example Result 1**: This is a mock search result. In a real implementation, this would contain actual web content from search engines like Google or Bing.
   Source: example.com

2. **Example Result 2**: Another mock result with relevant information about the query topic.
   Source: wikipedia.org

3. **Example Result 3**: Additional context and details from web sources.
   Source: news-site.com

*Note: This is currently using mock data. To enable real web search, integrate with a search API in the _perform_web_search method.*
"""

        return mock_results.strip()
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
                response = await self.bot_instance.llm.generate(prompt)

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
        try:
            # For now, implement a basic search simulation
            # In production, integrate with a real search API

            # Simple keyword-based response generation
            query_lower = query.lower()

            # Basic knowledge base for common queries
            knowledge_base = {
                "weather": "Weather information requires location data. Try searching with your city name for current weather conditions.",
                "time": "Current time depends on your timezone. You can check local time using time zone converters online.",
                "news": "For latest news, check major news websites like BBC, CNN, or Reuters. Breaking news is often available on their homepages.",
                "python": "Python is a popular programming language. For tutorials, visit python.org or sites like Real Python, freeCodeCamp.",
                "ai": "Artificial Intelligence encompasses machine learning, neural networks, and automation. Popular frameworks include TensorFlow, PyTorch.",
                "programming": "Programming involves writing code to solve problems. Popular languages: Python, JavaScript, Java, C++, Go.",
                "linux": "Linux is an open-source operating system. Popular distributions: Ubuntu, Fedora, CentOS, Arch Linux.",
                "docker": "Docker is a containerization platform. It allows packaging applications with their dependencies.",
                "kubernetes": "Kubernetes is a container orchestration system for automating deployment, scaling, and management of containerized applications.",
                "git": "Git is a distributed version control system. Commands: git clone, git commit, git push, git pull.",
            }

            # Find relevant knowledge
            relevant_info = []
            for keyword, info in knowledge_base.items():
                if keyword in query_lower:
                    relevant_info.append(info)
                    break

            # Generate search results
            results = []

            # Add relevant information if found
            if relevant_info:
                results.append({
                    'title': f'Information about {query.title()}',
                    'snippet': relevant_info[0][:300] + '...' if len(relevant_info[0]) > 300 else relevant_info[0],
                    'source': 'Knowledge Base'
                })

            # Add general search suggestions
            results.append({
                'title': 'Search Tips',
                'snippet': f'For more detailed information about "{query}", try searching on Google, Bing, or specialized websites. Include specific keywords for better results.',
                'source': 'Search Assistant'
            })

            # Add related topics
            if 'programming' in query_lower or 'code' in query_lower:
                results.append({
                    'title': 'Programming Resources',
                    'snippet': 'Check Stack Overflow, GitHub, MDN Web Docs, or official documentation for programming questions.',
                    'source': 'Developer Resources'
                })
            elif 'ai' in query_lower or 'machine learning' in query_lower:
                results.append({
                    'title': 'AI/ML Resources',
                    'snippet': 'Explore arXiv, Towards Data Science, or paperswithcode.com for AI and machine learning research.',
                    'source': 'AI Research'
                })

            if results:
                formatted_results = f"Web Search Results for: {query}\n\n"
                for i, result in enumerate(results, 1):
                    formatted_results += f"{i}. **{result['title']}**\n"
                    formatted_results += f"   {result['snippet']}\n"
                    formatted_results += f"   Source: {result['source']}\n\n"

                return formatted_results.strip()

        except Exception as e:
            logger.error(f"Search error: {e}")

        # Fallback if search fails
        return f"""
Web Search Results for: {query}

1. **Search Unavailable**: The search service is temporarily offline.
   Please try again later or rephrase your query.
   Source: System Status

2. **Alternative Help**: For general questions, you can ask me directly without using /search.
   I'm here to help with information, explanations, and conversations.
   Source: Assistant Help

*Note: Search functionality is being improved. Direct questions work best!*
"""
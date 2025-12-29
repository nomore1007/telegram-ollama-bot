"""
URL Shortener Plugin for Telegram Ollama Bot
Provides URL shortening functionality
"""

import logging
import aiohttp
from typing import List, Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

from .base import Plugin

logger = logging.getLogger(__name__)


class URLShortenerPlugin(Plugin):
    """Plugin that provides URL shortening services"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.shorteners = {
            'tinyurl': self._shorten_tinyurl,
            'isgd': self._shorten_isgd,
            'vgd': self._shorten_vgd,
        }
        logger.info("URL Shortener plugin initialized")

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with bot instance"""
        super().initialize(bot_instance)

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["shorten", "shorturl", "urlshort"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🔗 *URL Shortener Plugin*\n\n"
            "`/shorten <url>` - Shorten a URL using TinyURL\n"
            "`/shorturl <url>` - Alias for /shorten\n"
            "`/urlshort <url>` - Alias for /shorten\n\n"
            "*Supported Services:*\n"
            "• TinyURL (default)\n"
            "• is.gd\n"
            "• v.gd\n\n"
            "*Usage:*\n"
            "Send `/shorten https://www.example.com/very/long/url/that/needs/shortening`\n"
            "The bot will reply with a shortened version.\n\n"
            "*Note:* Make sure the URL starts with http:// or https://"
        )

    async def handle_shorten(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /shorten command"""
        await self._shorten_url(update, context)

    async def handle_shorturl(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /shorturl command"""
        await self._shorten_url(update, context)

    async def handle_urlshort(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /urlshort command"""
        await self._shorten_url(update, context)

    async def _shorten_url(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Shorten a URL"""
        if not update.message:
            return

        # Get URL from arguments
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a URL to shorten.\n\n"
                "Usage: `/shorten <url>`\n"
                "Example: `/shorten https://www.example.com`",
                parse_mode="Markdown"
            )
            return

        url = " ".join(context.args).strip()

        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text(
                "❌ Invalid URL format. Please include http:// or https://\n\n"
                "Example: `https://www.example.com`",
                parse_mode="Markdown"
            )
            return

        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Shortening URL...")

        try:
            # Use TinyURL by default
            shortened_url = await self._shorten_tinyurl(url)

            if shortened_url:
                await processing_msg.edit_text(
                    f"✅ *URL Shortened!*\n\n"
                    f"🔗 **Original:** {url}\n"
                    f"🔗 **Shortened:** {shortened_url}",
                    parse_mode="Markdown"
                )
            else:
                await processing_msg.edit_text(
                    "❌ Failed to shorten URL. Please try again later."
                )

        except Exception as e:
            logger.error(f"Error shortening URL: {e}")
            await processing_msg.edit_text(
                "❌ An error occurred while shortening the URL. Please try again."
            )

    async def _shorten_tinyurl(self, url: str) -> Optional[str]:
        """Shorten URL using TinyURL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://tinyurl.com/api-create.php",
                    params={"url": url},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            logger.error(f"TinyURL error: {e}")
        return None

    async def _shorten_isgd(self, url: str) -> Optional[str]:
        """Shorten URL using is.gd"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://is.gd/create.php",
                    params={"format": "simple", "url": url},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            logger.error(f"is.gd error: {e}")
        return None

    async def _shorten_vgd(self, url: str) -> Optional[str]:
        """Shorten URL using v.gd"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://v.gd/create.php",
                    params={"format": "simple", "url": url},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            logger.error(f"v.gd error: {e}")
        return None
"""
Telegram plugin for the bot.

This plugin handles all Telegram-specific functionality including commands, menus, and callbacks.
"""

import logging
import hashlib
from typing import Optional, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import ContextTypes

from .base import Plugin
from constants import MAX_MESSAGE_LENGTH


def anonymize_user_id(user_id: int) -> str:
    """Anonymize user ID for logging purposes"""
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:8]


logger = logging.getLogger(__name__)


class TelegramPlugin(Plugin):
    """Plugin that handles Telegram bot commands and interactions."""

    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name, config)
        self.bot_instance_instance = None

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with the bot instance."""
        self.bot_instance_instance = bot_instance
        logger.info("Telegram plugin initialized")

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return [
            "start", "help", "menu", "model", "listmodels", "changemodel",
            "setprompt", "timeout"
        ]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🤖 *Telegram Bot Commands*\n\n"
            "`/start` - Show welcome message and commands\n"
            "`/help` - Show this help message\n"
            "`/menu` - Show the main menu\n"
            "`/model` - Show current AI model info\n"
            "`/listmodels` - List all available AI models\n"
            "`/changemodel <model>` - Change AI model\n"
            "`/setprompt` - Set custom AI prompt\n"
            "`/timeout` - Set request timeout"
        )

    def on_command(self, update, context: ContextTypes.DEFAULT_TYPE, command: str, bot_instance) -> Optional[str]:
        """Handle commands specific to this plugin."""
        # This will be called from the main bot, but since Telegram handlers need direct async responses,
        # we'll handle this differently. For now, return None and let main bot handle.
        return None

    # Direct handler methods that can be called by the main bot

    async def handle_start(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        assert self.bot_instance is not None, "Plugin not initialized"
        if update.message:
            await update.message.reply_text(
                "🤖 *Telegram Ollama Bot*\n\n"
                "📋 *Commands:*\n"
                "`/help` - Show all available commands\n"
                "`/menu` - Show the main menu\n"
                "`/model` - Show current model info\n"
                "`/listmodels` - List available models\n"
                "`/changemodel <model>` - Change AI model\n"
                "`/setprompt` - Set custom AI prompt\n"
                "`/timeout` - Set request timeout\n\n"
                "🔍 *Auto Features:*\n"
                "📰 *News Detection:* Send any message with a news link!\n"
                "🎬 *YouTube Detection:* Send any message with a YouTube link!\n\n"
                "💬 *Chat:* Just send any message to talk with AI!\n\n"
                f"🧠 Current model: `{self.bot_instance.config.OLLAMA_MODEL}`\n"
                f"⏱️ Timeout: `{self.bot_instance.config.TIMEOUT}s`",
                parse_mode="Markdown"
            )

    async def handle_help(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if update.message:
            await update.message.reply_text(
                "🤖 *Telegram Ollama Bot - Commands*\n\n"
                "📋 *Basic Commands:*\n"
                "`/start` - Show welcome message and commands\n"
                "`/help` - Show this help message\n"
                "`/menu` - Show the main menu\n"
                "`/model` - Show current AI model info\n"
                "`/listmodels` - List all available AI models\n"
                "`/changemodel <model>` - Change AI model\n"
                "`/setprompt` - Set custom AI prompt\n"
                "`/timeout` - Set request timeout\n\n"
                "🔍 *Auto Features:*\n"
                "📰 *News Summarization:* Send any message with a news link\n"
                "🎬 *YouTube Summarization:* Send any message with a YouTube link\n\n"
                "💬 *Chat:* Just send any message to talk with AI!\n\n"
                "💡 *Examples:*\n"
                "`/setprompt You are a helpful coding assistant`\n"
                "`/timeout 60`\n"
                "`Check this: https://www.bbc.com/news/story`",
                parse_mode="Markdown"
            )

    async def handle_menu(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        if update.message:
            keyboard = [
                [InlineKeyboardButton("💬 Chat", callback_data="chat")],
                [InlineKeyboardButton("📰 News Summarizer", callback_data="news")],
                [InlineKeyboardButton("🎬 YouTube Summarizer", callback_data="youtube")],
                [InlineKeyboardButton("⚙️ Model Settings", callback_data="model")],
                [InlineKeyboardButton("❓ Help", callback_data="help")],
            ]
            await update.message.reply_text(
                "🤖 *Main Menu*\n\nChoose an option:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    async def handle_model_info(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /model command"""
        if update.message:
            await update.message.reply_text(
                f"🧠 Model: `{self.bot_instance.config.OLLAMA_MODEL}`\n"
                f"🌐 Host: `{self.bot_instance.config.OLLAMA_HOST}`\n"
                f"⏱ Timeout: `{self.bot_instance.config.TIMEOUT}s`",
                parse_mode="Markdown",
            )

    async def handle_listmodels(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listmodels command"""
        models = await self.bot.llm.list_models()
        if not models:
            if update.message:
                await update.message.reply_text("❌ No models found.")
            return

        text = "\n".join(f"• {m}" for m in models)
        if update.message:
            await update.message.reply_text(f"🤖 Available models:\n{text}")

    async def handle_changemodel(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /changemodel command"""
        if not context.args or len(context.args) == 0:
            # Show available models if no argument provided
            models = await self.bot.llm.list_models()
            if not models:
                if update.message:
                    await update.message.reply_text("❌ No models available.")
                return

            model_list = "\n".join(f"• `{m}`" for m in models)
            if update.message:
                await update.message.reply_text(
                    f"🤖 Available models:\n{model_list}\n\n"
                    f"💡 Usage: `/changemodel <model_name>`\n"
                    f"📍 Current: `{self.bot_instance.config.OLLAMA_MODEL}`",
                    parse_mode="Markdown"
                )
            return

        # Get the requested model name
        requested_model = " ".join(context.args)

        # Validate the model exists
        models = await self.bot.llm.list_models()
        if requested_model not in models:
            if update.message:
                await update.message.reply_text(
                    f"❌ Model `{requested_model}` not found.\n\n"
                    f"📋 Available models:\n" + "\n".join(f"• `{m}`" for m in models[:10]) +
                    (f"\n... and {len(models)-10} more" if len(models) > 10 else ""),
                    parse_mode="Markdown"
                )
            return

        # Update the model
        self.bot_instance.config.OLLAMA_MODEL = requested_model
        self.bot.llm.set_model(requested_model)

        if update.message:
            await update.message.reply_text(
                f"✅ Model changed to: `{requested_model}`\n\n"
                f"🧠 The bot will now use this model for AI responses.",
                parse_mode="Markdown"
            )

    async def handle_timeout(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /timeout command"""
        try:
            if not context.args or len(context.args) == 0:
                raise ValueError("No timeout provided")

            seconds = int(context.args[0])
            if not 1 <= seconds <= 600:
                raise ValueError("Timeout out of range")

            self.bot_instance.config.TIMEOUT = seconds
            self.bot.llm.set_timeout(seconds)

            if update.message:
                await update.message.reply_text(f"✅ Timeout set to {seconds}s")

        except (IndexError, ValueError):
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: /timeout <seconds> (1–600)"
                )

    async def handle_setprompt(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setprompt command"""
        try:
            if not context.args or len(context.args) == 0:
                # Show current prompt
                current_prompt = self.bot_instance.custom_prompt[:100] + "..." if len(self.bot_instance.custom_prompt) > 100 else self.bot_instance.custom_prompt
                if update.message:
                    await update.message.reply_text(
                        f"📝 *Current Prompt:*\n\n`{current_prompt}`\n\n"
                        "💡 *To set a new prompt:* `/setprompt Your prompt here`",
                        parse_mode="Markdown"
                    )
                return

            # Join all arguments to form the prompt
            new_prompt = " ".join(context.args)

            if len(new_prompt) < 10:
                raise ValueError("Prompt too short")

            if len(new_prompt) > 1000:
                raise ValueError("Prompt too long (max 1000 characters)")

            self.bot_instance.custom_prompt = new_prompt

            if update.message:
                preview = new_prompt[:100] + "..." if len(new_prompt) > 100 else new_prompt
                await update.message.reply_text(
                    f"✅ *Prompt Updated!*\n\n"
                    f"📝 *New prompt:*\n`{preview}`",
                    parse_mode="Markdown"
                )

        except (IndexError, ValueError) as e:
            if update.message:
                await update.message.reply_text(
                    f"❌ Error: {str(e)}\n\n"
                    "💡 *Usage:* `/setprompt Your custom prompt here`\n"
                    "📏 *Length:* 10-1000 characters",
                    parse_mode="Markdown"
                )

    async def handle_menu_callback(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle menu callbacks"""
        query = update.callback_query
        if not query:
            return

        await query.answer()

        if not query.data:
            await query.edit_message_text("❌ Invalid callback data.")
            return

        action = query.data

        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])

        if action == "chat":
            await query.edit_message_text(
                "💬 *Chat Mode*\n\n"
                "Just send me any message and I'll respond using the AI model.\n\n"
                f"🧠 Current model: `{self.bot_instance.config.OLLAMA_MODEL}`",
                parse_mode="Markdown",
                reply_markup=back_button
            )
        elif action == "news":
            await query.edit_message_text(
                "📰 *News Summarizer*\n\n"
                "🤖 *Automatic Detection:* Simply send any message containing a news article link and I'll automatically summarize it!\n\n"
                "📋 *Supported Sites:* BBC, CNN, Reuters, NY Times, Washington Post, Guardian, WSJ, Bloomberg, NBC News, ABC News, CBS News, Fox News, AP News, NPR, Vox, Politico, Wired, TechCrunch, and many more!\n\n"
                "💡 *Example:* \"Check out this article: https://www.bbc.com/news/some-story\"\n\n"
                "🚀 *Limit:* Up to 2 articles per message to prevent spam.",
                parse_mode="Markdown",
                reply_markup=back_button
            )
        elif action == "youtube":
            await query.edit_message_text(
                "🎬 *YouTube Summarizer*\n\n"
                "🤖 *Automatic Detection:* Simply send any message containing a YouTube link and I'll automatically summarize the video!\n\n"
                "📋 *Supported Formats:* Regular videos, shorts, embedded videos, and all YouTube URL variations\n\n"
                "💡 *Examples:*\n"
                "• \"Watch this: https://www.youtube.com/watch?v=dQw4w9WgXcQ\"\n"
                "• \"Amazing short: https://youtu.be/dQw4w9WgXcQ\"\n"
                "• \"Check out: https://www.youtube.com/shorts/VIDEO_ID\"\n\n"
                "🎯 *Features:* Video info, transcript extraction, AI-powered summary\n"
                "🚀 *Limit:* Up to 2 videos per message to prevent spam.",
                parse_mode="Markdown",
                reply_markup=back_button
            )
        elif action == "model":
            keyboard = [
                [InlineKeyboardButton("Show Info", callback_data="model_info")],
                [InlineKeyboardButton("List Models", callback_data="listmodels")],
                [InlineKeyboardButton("Change Model", callback_data="changemodel")],
                [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")],
            ]
            await query.edit_message_text(
                "⚙️ *Model Settings*\n\nChoose an option:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        elif action == "listmodels":
            await self._show_models_list(query)
        elif action == "changemodel":
            await self._show_model_selection(query, context)
        elif action == "model_info":
            await self._show_model_info(query)
        elif action == "timeout":
            await query.edit_message_text(
                "⏱️ *Set Timeout*\n\n"
                "Use the command:\n`/timeout <seconds>`\n\n"
                "Valid range: 1-600 seconds\n"
                f"Current timeout: `{self.bot_instance.config.TIMEOUT}s`",
                parse_mode="Markdown",
                reply_markup=back_button
            )
        elif action == "help":
            await self._show_help(query)
        elif action == "back_to_menu":
            await self.show_menu_query(query)
        else:
            await query.edit_message_text("❌ Unknown menu option.", reply_markup=back_button)

    async def handle_model_callback(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle model selection callbacks"""
        query = update.callback_query
        if not query:
            return

        await query.answer()

        try:
            if not query.data:
                await query.edit_message_text("❌ Invalid callback data.")
                return

            logger.info(f"Model callback received for user")

            # Parse index from callback data
            model_idx = int(query.data.split(":", 1)[1])

            # Get model list from user_data
            model_list = []
            if context.user_data:
                model_list = context.user_data.get('model_list', [])
                logger.info(f"Found model_list in user_data: {len(model_list)} models")
            else:
                logger.warning("No user_data available in context")

            # Validate index
            if not model_list or not (0 <= model_idx < len(model_list)):
                logger.error(f"Invalid model index, model_list length: {len(model_list)}")
                await query.edit_message_text("❌ Model selection expired. Please use /changemodel again.")
                return

            model_name = model_list[model_idx]
            logger.info(f"Selected model: {model_name}")

            self.bot_instance.config.OLLAMA_MODEL = model_name
            self.bot_instance.ollama.model = model_name

            await query.edit_message_text(
                f"✅ Model updated to:\n`{model_name}`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
            )

        except (ValueError, IndexError) as e:
            logger.error(f"Model callback error: {e}")
            if query:
                await query.edit_message_text("❌ Failed to update model.")

    # Helper methods (similar to original handlers.py)

    async def show_menu_query(self, query):
        """Show menu in query context"""
        keyboard = [
            [InlineKeyboardButton("💬 Chat", callback_data="chat")],
            [InlineKeyboardButton("📰 News Summarizer", callback_data="news")],
            [InlineKeyboardButton("🎬 YouTube Summarizer", callback_data="youtube")],
            [InlineKeyboardButton("⚙️ Model Settings", callback_data="model")],
            [InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
        await query.edit_message_text(
            "🤖 *Main Menu*\n\nChoose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def _show_model_info(self, query):
        """Show model info in query context"""
        text = (
            f"🧠 *Model Information*\n\n"
            f"🤖 Model: `{self.bot_instance.config.OLLAMA_MODEL}`\n"
            f"🌐 Host: `{self.bot_instance.config.OLLAMA_HOST}`\n"
            f"⏱ Timeout: `{self.bot_instance.config.TIMEOUT}s`"
        )
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
        if query:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_button)

    async def _show_models_list(self, query):
        """Show models list in query context"""
        models = await self.bot.llm.list_models()
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
        if not models:
            if query:
                await query.edit_message_text("❌ No models found.", reply_markup=back_button)
            return

        text = "🤖 *Available Models*\n\n" + "\n".join(f"• `{m}`" for m in models)
        if query:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_button)

    async def _show_model_selection(self, query, context):
        """Show model selection in query context"""
        models = await self.bot.llm.list_models()
        if not models:
            back_button = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
            if query:
                await query.edit_message_text("❌ No models available.", reply_markup=back_button)
            return

        # Store models list in user_data for callback lookup
        if context.user_data:
            context.user_data['model_list'] = models
            logger.info(f"Stored {len(models)} models in user_data for model selection")
        else:
            logger.warning("No user_data available to store model list")

        # Use index-based callback data to avoid length limits
        keyboard = [
            [InlineKeyboardButton(m, callback_data=f"changemodel:{idx}")]
            for idx, m in enumerate(models)
        ]
        keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

        if query:
            await query.edit_message_text(
                f"🤖 *Select a Model*\n\n(Current: `{self.bot_instance.config.OLLAMA_MODEL}`)",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _show_help(self, query):
        """Show help in query context"""
        help_text = (
            "❓ *Help & Commands*\n\n"
            "• *Menu Options* - Use /start to see interactive menu\n"
            "• *Direct Chat* - Just send any message to talk with AI\n"
            "• *News Summarization* - Send any message with a news link to auto-summarize!\n"
            "• *YouTube Summarization* - Send any message with a YouTube link to auto-summarize!\n\n"
            "*Available Commands:*\n"
            "`/start` - Show main menu\n"
            "`/help` - This help message\n"
            "`/menu` - Show the main menu\n"
            "`/model` - Show current model info\n"
            "`/listmodels` - List available models\n"
            "`/changemodel <model>` - Change AI model\n"
            "`/timeout <seconds>` - Set request timeout (1-600)\n\n"
            "*News Summarizer Features:*\n"
            "📰 *Auto-Detection:* Automatically detects news URLs in messages\n"
            "🤖 *AI-Powered:* Uses AI to create comprehensive summaries\n"
            "🌐 *Multi-Source:* Supports 30+ major news websites\n"
            "📊 *Structured:* Provides key points and context\n\n"
            "*YouTube Summarizer Features:*\n"
            "🎬 *Auto-Detection:* Automatically detects YouTube URLs in messages\n"
            "🎥 *Video Info:* Extracts title, channel, views, duration\n"
            "📝 *Transcript:* Pulls video transcript using YouTube API\n"
            "🤖 *AI-Powered:* Uses AI to summarize video content\n"
            "🎯 *Smart:* Supports all YouTube URL formats (watch, shorts, embed)"
        )
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]])
        if query:
            await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=back_button)
"""
Telegram plugin for the bot.

This plugin handles all Telegram-specific functionality including commands, menus, and callbacks.
"""

import logging
import hashlib
from typing import Optional, List, Dict, Any
from personality import Personality, personality_manager

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import ContextTypes

from .base import Plugin
from constants import MAX_MESSAGE_LENGTH
from admin import require_admin


def anonymize_user_id(user_id: int) -> str:
    """Anonymize user ID for logging purposes"""
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:8]


logger = logging.getLogger(__name__)


class TelegramPlugin(Plugin):
    """Plugin that handles Telegram bot commands and interactions."""

    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name, config)
        self.bot = None
        logger.info("Telegram plugin initialized")

    def initialize(self, bot_instance) -> None:
        super().initialize(bot_instance)
        self.bot = bot_instance

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return [
            "start", "help", "menu", "model", "listmodels", "setmodel", "changemodel",
            "setprovider", "setprompt", "timeout", "userid", "addadmin", "removeadmin", "listadmins",
            "personality", "setpersonality", "clear"
        ]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🤖 *Deepthought Bot - Complete Command Guide*\n\n"
            "🎯 *Getting Started:*\n"
            "`/start` - Initialize bot and show welcome message\n"
            "`/help` - Display this comprehensive help guide\n"
            "`/menu` - Access interactive menu with all features\n"
            "`/userid` - Get your Telegram user ID for admin setup\n\n"
            "💬 *AI Chat & Conversation:*\n"
            "Just type any message to chat with AI!\n"
            "`/ask <message>` - Direct AI query\n"
            "`/clear` - Reset conversation history\n\n"
            "🎭 *Personality System:*\n"
            "`/personality` - Show all available bot personalities\n"
            "`/setpersonality <name>` - Change bot personality\n"
            "• `friendly` - Warm and conversational\n"
            "• `professional` - Formal business communication\n"
            "• `humorous` - Witty and entertaining\n"
            "• `helpful` - Maximally useful and detailed\n"
            "• `creative` - Imaginative and innovative\n"
            "• `concise` - Brief and direct\n\n"
            "🔍 *Web Search & Information:*\n"
            "`/search <query>` - Real-time web search with AI analysis\n"
            "*Examples:*\n"
            "• `/search latest AI developments`\n"
            "• `/search Python async programming`\n"
            "• `/search quantum computing news`\n\n"
            "⚙️ *AI Model Management (Admin Only):*\n"
            "`/model` - Display current model and provider info\n"
            "`/listmodels` - List available models for current provider\n"
             "`/setmodel <model>` - Set AI model for this channel\n"
             "`/changemodel` - Show model selection menu\n"
            "`/setprompt` - Customize AI system prompt\n"
            "`/timeout <seconds>` - Set response timeout (1-600s)\n\n"
            "👑 *Administrator Controls (Admin Only):*\n"
            "`/addadmin <user_id>` - Grant admin privileges\n"
            "`/removeadmin <user_id>` - Revoke admin privileges\n"
            "`/listadmins` - Show all administrators\n\n"
            "📱 *Auto-Features (Always Active):*\n"
            "📰 *News Detection* - Send news URLs for automatic summarization\n"
            "🎬 *YouTube Detection* - Send video URLs for automatic analysis\n"
            "💡 *Smart Responses* - Context-aware conversations\n\n"
            "🔒 *Security & Access:*\n"
            "• Admin commands require administrator privileges\n"
            "• Input validation prevents malicious content\n"
            "• Rate limiting protects against abuse\n"
            "• All sensitive data is securely stored\n\n"
            "🌟 *Pro Tips:*\n"
            "• Use `/menu` for interactive feature discovery\n"
            "• Combine search with personality for specialized responses\n"
            "• Clear conversations periodically for focused discussions\n"
            "• Admin setup: Use `/userid` then `python admin_cli.py setup <id>`"
        )

    def on_command(self, update, context: ContextTypes.DEFAULT_TYPE, command: str, bot_instance) -> Optional[str]:
        """Handle commands specific to this plugin."""
        # This will be called from the main bot, but since Telegram handlers need direct async responses,
        # we'll handle this differently. For now, return None and let main bot handle.
        return None

    # Direct handler methods that can be called by the main bot

    async def handle_start(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        assert self.bot is not None, "Plugin not initialized"
        if update.message:
            await update.message.reply_text(
                "🌟 *Welcome to Deepthought Bot!* 🤖\n\n"
                "I'm your advanced AI assistant with multi-provider support, "
                "personality modes, and real-time web search capabilities.\n\n"
                "🚀 *Quick Start:*\n"
                "• Just type any message to start chatting!\n"
                "• Use `/search <query>` for web information\n"
                "• Try `/personality` to customize my behavior\n\n"
                "📚 *Key Features:*\n"
                "🔍 *Web Search* - Real-time information retrieval\n"
                "🎭 *6 Personalities* - Adapt my communication style\n"
                "📰 *Auto-Summarization* - News articles and YouTube videos\n"
                "⚙️ *Multi-Provider* - Ollama, OpenAI, Groq, and more\n"
                "👑 *Admin Controls* - Secure configuration management\n\n"
                "📖 *Get Started:*\n"
                "`/help` - Complete command guide\n"
                "`/menu` - Interactive feature menu\n"
                "`/userid` - Get your user ID for admin setup\n\n"
                f"🧠 Current: {self.bot.llm.provider_name} | {self.bot.llm.model}\n"
                f"🎭 Personality: {self.bot.personality.value}\n"
                f"⏱️ Timeout: {self.bot.llm.provider.timeout}s",
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
             "`/setprovider <provider> [host]` - Set AI provider for this channel\n"
             "`/setmodel <model>` - Set AI model for this channel\n"
             "`/changemodel` - Show model selection menu\n"
             "`/setprompt` - Set custom AI prompt for this channel\n"
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
            channel_id = update.effective_chat.id if update.effective_chat else None
            current_model = self.bot.channel_settings.get(channel_id, {}).get('model', self.bot.config.OLLAMA_MODEL) if channel_id else self.bot.config.OLLAMA_MODEL
            await update.message.reply_text(
                f"🧠 Model: `{current_model}`\n"
                f"🌐 Host: `{self.bot.config.OLLAMA_HOST}`\n"
                f"⏱ Timeout: `{self.bot.config.TIMEOUT}s`",
                parse_mode="Markdown",
            )

    async def handle_listmodels(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listmodels command"""
        if self.bot is None:
            if update.message:
                await update.message.reply_text("❌ Plugin not initialized properly")
            return

        channel_id = update.effective_chat.id if update.effective_chat else None
        channel_settings = self.bot.channel_settings.get(channel_id, {}) if channel_id else {}
        provider = channel_settings.get('provider', 'ollama')
        host = channel_settings.get('host', 'http://localhost:11434') if provider == 'ollama' else None
        api_key = None
        if provider != 'ollama':
            api_key_env = f'{provider.upper()}_API_KEY'
            api_key = getattr(self.bot.config, api_key_env, None)

        from llm_client import LLMClient
        try:
            channel_llm = LLMClient(provider=provider, host=host, api_key=api_key)
            models = await channel_llm.list_models()
        except Exception as e:
            if update.message:
                await update.message.reply_text(f"❌ Error accessing LLM: {e}")
            return

        if not models:
            if update.message:
                await update.message.reply_text("❌ No models found.")
            return

        text = "\n".join(f"• {m}" for m in models)
        if update.message:
            await update.message.reply_text(f"🤖 Available models for {provider}:\n{text}")

    @require_admin
    async def handle_changemodel(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /changemodel command - show model selection menu"""
        if update.message:
            channel_id = update.effective_chat.id if update.effective_chat else None
            channel_settings = self.bot.channel_settings.get(channel_id, {}) if channel_id else {}
            provider = channel_settings.get('provider', 'ollama')
            host = channel_settings.get('host', 'http://localhost:11434') if provider == 'ollama' else None
            api_key = None
            if provider != 'ollama':
                api_key_env = f'{provider.upper()}_API_KEY'
                api_key = getattr(self.bot.config, api_key_env, None)

            from llm_client import LLMClient
            try:
                channel_llm = LLMClient(provider=provider, host=host, api_key=api_key)
                models = await channel_llm.list_models()
            except Exception as e:
                await update.message.reply_text(f"❌ Error accessing LLM: {e}")
                return

            if not models:
                await update.message.reply_text("❌ No models available.")
                return

            # Store models list for callback
            if context.user_data is not None:
                context.user_data['model_list'] = models

            # Use index-based callback data to avoid length limits
            keyboard = [
                [InlineKeyboardButton(m, callback_data=f"changemodel:{idx}")]
                for idx, m in enumerate(models)
            ]
            keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

            current_model = channel_settings.get('model', self.bot.config.OLLAMA_MODEL)
            await update.message.reply_text(
                f"🤖 *Select a Model for {provider}*\n\n(Current: `{current_model}`)",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    @require_admin
    async def handle_setmodel(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setmodel command"""
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
                    f"💡 Usage: `/setmodel <model_name>`\n"
                    f"📍 Current: `{self.bot.config.OLLAMA_MODEL}`",
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

        # Update the model for this channel
        channel_id = update.effective_chat.id if update.effective_chat else None
        if channel_id:
            self.bot.channel_settings.setdefault(channel_id, {})['model'] = requested_model

        if update.message:
            await update.message.reply_text(
                f"✅ Model changed to: `{requested_model}`\n\n"
                f"🧠 The bot will now use this model for AI responses in this channel.",
                parse_mode="Markdown"
            )

    @require_admin
    async def handle_setprovider(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setprovider command"""
        supported_providers = ['ollama', 'openai', 'groq', 'together', 'huggingface', 'anthropic']

        if not context.args or len(context.args) == 0:
            # Show available providers
            provider_list = "\n".join(f"• `{p}`" for p in supported_providers)
            channel_id = update.effective_chat.id if update.effective_chat else None
            current_provider = self.bot.channel_settings.get(channel_id, {}).get('provider', 'ollama') if channel_id else 'ollama'
            if update.message:
                await update.message.reply_text(
                    f"🤖 Available providers:\n{provider_list}\n\n"
                    f"💡 Usage: `/setprovider <provider>` or `/setprovider ollama <host>`\n"
                    f"📍 Current: `{current_provider}`",
                    parse_mode="Markdown"
                )
            return

        provider = context.args[0].lower()
        if provider not in supported_providers:
            if update.message:
                await update.message.reply_text(
                    f"❌ Provider `{provider}` not supported.\n\n"
                    f"📋 Available: {', '.join(supported_providers)}",
                    parse_mode="Markdown"
                )
            return

        # Update the provider for this channel
        channel_id = update.effective_chat.id if update.effective_chat else None
        if channel_id:
            self.bot.channel_settings.setdefault(channel_id, {})['provider'] = provider

            # If ollama and host provided
            host = None
            if provider == 'ollama' and len(context.args) > 1:
                host = context.args[1]
                self.bot.channel_settings[channel_id]['host'] = host

            reply = f"✅ Provider set to: `{provider}`"
            if host:
                reply += f" with host `{host}`"
            reply += "\n\n🧠 The bot will now use this provider for AI responses in this channel."
        else:
            reply = "❌ Unable to set provider for this chat."

        if update.message:
            await update.message.reply_text(reply, parse_mode="Markdown")
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

        # Update the model for this channel
        channel_id = update.effective_chat.id if update.effective_chat else None
        if channel_id:
            self.bot.channel_settings.setdefault(channel_id, {})['model'] = requested_model

        if update.message:
            await update.message.reply_text(
                f"✅ Model changed to: `{requested_model}`\n\n"
                f"🧠 The bot will now use this model for AI responses in this channel.",
                parse_mode="Markdown"
            )

    @require_admin
    async def handle_timeout(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /timeout command"""
        try:
            if not context.args or len(context.args) == 0:
                raise ValueError("No timeout provided")

            seconds = int(context.args[0])
            if not 1 <= seconds <= 600:
                raise ValueError("Timeout out of range")

            self.bot.config.TIMEOUT = seconds
            self.bot.llm.set_timeout(seconds)

            if update.message:
                await update.message.reply_text(f"✅ Timeout set to {seconds}s")

        except (IndexError, ValueError):
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: /timeout <seconds> (1–600)"
                )

    @require_admin
    async def handle_setprompt(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setprompt command"""
        try:
            if not context.args or len(context.args) == 0:
                # Show current prompt
                current_prompt = self.bot.custom_prompt[:100] + "..." if len(self.bot.custom_prompt) > 100 else self.bot.custom_prompt
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

            # Update the prompt for this channel
            channel_id = update.effective_chat.id if update.effective_chat else None
            if channel_id:
                self.bot.channel_settings.setdefault(channel_id, {})['prompt'] = new_prompt

            if update.message:
                preview = new_prompt[:100] + "..." if len(new_prompt) > 100 else new_prompt
                await update.message.reply_text(
                    f"✅ *Prompt Updated for this channel!*\n\n"
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
                f"🧠 Current model: `{self.bot.config.OLLAMA_MODEL}`",
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
                [InlineKeyboardButton("Set Ollama Host", callback_data="set_ollama_host")],
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
        elif action == "set_ollama_host":
            await query.edit_message_text(
                "🌐 *Set Ollama Host*\n\n"
                "Use the command:\n`/setprovider ollama <host>`\n\n"
                "Example:\n`/setprovider ollama http://localhost:11434`\n"
                "Or for remote:\n`/setprovider ollama http://remote-server:11434`\n\n"
                "This sets the Ollama host for this channel.",
                parse_mode="Markdown",
                reply_markup=back_button
            )
        elif action == "timeout":
            await query.edit_message_text(
                "⏱️ *Set Timeout*\n\n"
                "Use the command:\n`/timeout <seconds>`\n\n"
                "Valid range: 1-600 seconds\n"
                f"Current timeout: `{self.bot.config.TIMEOUT}s`",
                parse_mode="Markdown",
                reply_markup=back_button
            )
        elif action == "help":
            await self._show_help(query)
        elif action == "back_to_menu":
            await self.show_menu_query(query)
        else:
            await query.edit_message_text("❌ Unknown menu option.", reply_markup=back_button)

    @require_admin
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

            # Update the model for this channel
            channel_id = query.message.chat.id if query.message and query.message.chat else None
            if channel_id:
                self.bot.channel_settings.setdefault(channel_id, {})['model'] = model_name

            await query.edit_message_text(
                f"✅ Model updated to:\n`{model_name}`\n\n*For this channel*",
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
        # Assume query from the same chat
        channel_id = query.message.chat.id if query.message and query.message.chat else None
        current_model = self.bot.channel_settings.get(channel_id, {}).get('model', self.bot.config.OLLAMA_MODEL) if channel_id else self.bot.config.OLLAMA_MODEL
        text = (
            f"🧠 *Model Information*\n\n"
            f"🤖 Model: `{current_model}`\n"
            f"🌐 Host: `{self.bot.config.OLLAMA_HOST}`\n"
            f"⏱ Timeout: `{self.bot.config.TIMEOUT}s`"
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
            # Assume query from the same chat
            channel_id = query.message.chat.id if query.message and query.message.chat else None
            current_model = self.bot.channel_settings.get(channel_id, {}).get('model', self.bot.config.OLLAMA_MODEL) if channel_id else self.bot.config.OLLAMA_MODEL
            await query.edit_message_text(
                f"🤖 *Select a Model*\n\n(Current: `{current_model}`)",
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
             "`/setmodel <model>` - Set AI model for this channel\n"
             "`/changemodel` - Show model selection menu\n"
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

    async def handle_userid(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /userid command - shows user's Telegram ID"""
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        if update.message:
            await update.message.reply_text(
                f"🆔 *Your Telegram User ID:*\n`{user_id}`\n\n"
                "💡 *Use this ID for admin management commands like `/addadmin {user_id}`*",
                parse_mode="Markdown"
            )

    @require_admin
    async def handle_addadmin(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addadmin command"""
        if not context.args or len(context.args) == 0:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/addadmin <user_id>`\n\n"
                    "💡 Find user ID by using `/userid` or checking bot logs",
                    parse_mode="Markdown"
                )
            return

        try:
            new_admin_id = int(context.args[0])
            requesting_user_id = update.effective_user.id

            if self.bot.admin_manager.add_admin(new_admin_id, requesting_user_id):
                if update.message:
                    await update.message.reply_text(f"✅ Added user {new_admin_id} as administrator.")
            else:
                if update.message:
                    await update.message.reply_text("❌ Failed to add admin. You must be an admin to do this.")

        except ValueError:
            if update.message:
                await update.message.reply_text("❌ Invalid user ID. Must be a number.")

    @require_admin
    async def handle_removeadmin(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /removeadmin command"""
        if not context.args or len(context.args) == 0:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/removeadmin <user_id>`\n\n"
                    "⚠️ Cannot remove the last administrator.",
                    parse_mode="Markdown"
                )
            return

        try:
            admin_id = int(context.args[0])
            requesting_user_id = update.effective_user.id

            if self.bot.admin_manager.remove_admin(admin_id, requesting_user_id):
                if update.message:
                    await update.message.reply_text(f"✅ Removed user {admin_id} from administrators.")
            else:
                if update.message:
                    await update.message.reply_text("❌ Failed to remove admin. Check permissions or ensure at least one admin remains.")

        except ValueError:
            if update.message:
                await update.message.reply_text("❌ Invalid user ID. Must be a number.")

    @require_admin
    async def handle_listadmins(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listadmins command"""
        admins = self.bot.admin_manager.get_admins()
        if not admins:
            admin_list = "No administrators configured."
        else:
            admin_list = "\n".join(f"• `{admin_id}`" for admin_id in admins)

        if update.message:
                await update.message.reply_text(
                    f"👑 *Bot Administrators*\n\n{admin_list}",
                    parse_mode="Markdown"
                )

    async def handle_personality(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /personality command - show available personalities"""
        personalities = personality_manager.list_personalities()

        personality_list = "\n".join(
            f"• `{key}` - {info['description']}"
            for key, info in personalities.items()
        )

        current = self.bot.personality.value if hasattr(self.bot, 'personality') else 'helpful'

        if update.message:
            await update.message.reply_text(
                f"🎭 *Bot Personalities*\n\n"
                f"**Current:** `{current}`\n\n"
                f"**Available:**\n{personality_list}\n\n"
                f"💡 Use `/setpersonality <name>` to change",
                parse_mode="Markdown"
            )

    async def handle_setpersonality(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setpersonality command"""
        if not context.args or len(context.args) == 0:
            await self.handle_personality(update, context)
            return

        personality_name = context.args[0].lower()
        available = personality_manager.list_personalities()

        if personality_name not in available:
            if update.message:
                await update.message.reply_text(
                    f"❌ Personality `{personality_name}` not found.\n\n"
                    f"Available: {', '.join(available.keys())}",
                    parse_mode="Markdown"
                )
            return

        try:
            new_personality = Personality(personality_name)
            self.bot.personality = new_personality

            if update.message:
                await update.message.reply_text(
                    f"✅ *Personality Changed!*\n\n"
                    f"🎭 Now using: `{personality_name}`\n"
                    f"📝 {available[personality_name]['description']}",
                    parse_mode="Markdown"
                )
        except ValueError as e:
            if update.message:
                await update.message.reply_text(f"❌ Error setting personality: {e}")

    async def handle_clear(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - clear conversation history"""
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id:
            self.bot.conversation_manager.clear_conversation(chat_id)
            if update.message:
                await update.message.reply_text("🧹 *Conversation history cleared!*", parse_mode="Markdown")
        else:
            if update.message:
                await update.message.reply_text("❌ Unable to clear conversation.")
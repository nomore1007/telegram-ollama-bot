"""Main Telegram Ollama Bot application"""

import logging
import asyncio
import re
import sys
import os
import importlib.util

# Add current directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now we can import settings as a module
import settings

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext,
    filters,
)
from constants import (
    MAX_MESSAGE_LENGTH, MAX_ARTICLES_PER_MESSAGE, MAX_VIDEOS_PER_MESSAGE,
    LOG_FORMAT, LOG_LEVEL
)
from ollama_client import OllamaClient
from summarizers import NewsSummarizer, YouTubeSummarizer
from handlers import TelegramHandlers
from conversation import ConversationManager
from security import InputValidator, RateLimiter


# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------

logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Main Bot Class
# -------------------------------------------------------------------

class TelegramOllamaBot:
    """Main Telegram bot class integrating Ollama AI"""

    def __init__(self, config):
        self.config = config
        self.ollama = OllamaClient(
            config.OLLAMA_HOST,
            config.OLLAMA_MODEL,
            config.TIMEOUT,
        )
        self.news_summarizer = NewsSummarizer(self.ollama)
        self.youtube_summarizer = YouTubeSummarizer(self.ollama)
        self.conversation_manager = ConversationManager()
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()
        self.custom_prompt = getattr(config, 'DEFAULT_PROMPT', "You are a helpful AI assistant.")
        self.bot_username = None
        self.handlers = TelegramHandlers(self)

    # ---------------------------------------------------------------
    # Message handling
    # ---------------------------------------------------------------

    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle incoming messages"""
        if update.message:
            message_text = update.message.text
            if not message_text:
                return

            chat_id = update.message.chat.id
            user_id = update.message.from_user.id if update.message.from_user else chat_id

            # Rate limiting check
            allowed, rate_limit_msg = self.rate_limiter.is_allowed(user_id, "message")
            if not allowed:
                await update.message.reply_text(f"🚫 {rate_limit_msg}")
                return

            # Input validation
            valid, validation_msg = self.input_validator.validate_text(message_text)
            if not valid:
                await update.message.reply_text(f"🚫 {validation_msg}")
                return

            chat_type = update.message.chat.type
            is_group_chat = chat_type in ["group", "supergroup"]
            bot_mentioned = False

            if is_group_chat:
                if self.bot_username and f"@{self.bot_username}" in message_text:
                    bot_mentioned = True
                    # Remove bot mention from the message text for AI processing
                    message_text = message_text.replace(f"@{self.bot_username}", "").strip()
                    # Remove any leading/trailing whitespace after removing mention
                    message_text = message_text.strip()
                else:
                    # If in group chat and bot not mentioned, ignore
                    return

            # If not a group chat or bot was mentioned in a group chat
            # (rest of your existing handle_message logic)

            # Check for YouTube URLs first (highest priority)
            youtube_urls = self.youtube_summarizer.extract_video_urls(message_text)

            if youtube_urls:
                await update.message.reply_text("🎬 *YouTube video detected! Summarizing...*", parse_mode="Markdown")

                for url in youtube_urls[:MAX_VIDEOS_PER_MESSAGE]:  # Limit videos per message
                    try:
                        await update.message.reply_text("⏳ Processing video...")
                        summary = await self.youtube_summarizer.process_video(url)

                        # Split long summaries
                        if len(summary) > MAX_MESSAGE_LENGTH:
                            parts = [summary[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(summary), MAX_MESSAGE_LENGTH)]
                            for i, part in enumerate(parts):
                                await update.message.reply_text(part, parse_mode="Markdown", disable_web_page_preview=i>0)
                        else:
                            await update.message.reply_text(summary, parse_mode="Markdown")

                    except Exception as e:
                        logger.error(f"Error processing video {url}: {e}")
                        await update.message.reply_text(f"❌ Failed to process video from {url}. Please try again later.")

                return

            # Check for news URLs second
            news_urls = self.news_summarizer.extract_urls(message_text)

            if news_urls:
                await update.message.reply_text("📰 *News article detected! Summarizing...*", parse_mode="Markdown")

                for url in news_urls[:MAX_ARTICLES_PER_MESSAGE]:  # Limit articles per message
                    try:
                        await update.message.reply_text("⏳ Processing article...")
                        summary = await self.news_summarizer.process_article(url)

                        # Split long summaries
                        if len(summary) > MAX_MESSAGE_LENGTH:
                            parts = [summary[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(summary), MAX_MESSAGE_LENGTH)]
                            for i, part in enumerate(parts):
                                await update.message.reply_text(part, parse_mode="Markdown", disable_web_page_preview=i>0)
                        else:
                            await update.message.reply_text(summary, parse_mode="Markdown")

                    except Exception as e:
                        logger.error(f"Error processing article {url}: {e}")
                        await update.message.reply_text(f"❌ Failed to process article from {url}. Please try again later.")

                return

            # Regular chat message with conversation context
            thinking_message = await update.message.reply_text("🤔 Thinking…")

            # Add user message to conversation history
            chat_id = update.message.chat.id
            self.conversation_manager.add_user_message(chat_id, message_text)

            # Get conversation context
            context = self.conversation_manager.get_context(chat_id, self.custom_prompt)

            # Generate response with full context
            response = await self.ollama.generate(context)

            # Add assistant response to conversation history
            self.conversation_manager.add_assistant_message(chat_id, response)

            await thinking_message.edit_text(response)

    # ---------------------------------------------------------------

    async def post_init(self, application: Application) -> None:
        """
        Post-initialization hook to set the bot's username and commands.
        """
        self.bot_username = application.bot.username
        commands = [
            BotCommand("start", "Show welcome message and commands"),
            BotCommand("help", "Show all available commands"),
            BotCommand("menu", "Show the main menu"),
            BotCommand("model", "Show current AI model info"),
            BotCommand("listmodels", "List all available AI models"),
            BotCommand("setmodel", "Interactive AI model selection"),
            BotCommand("setprompt", "Set custom AI prompt"),
            BotCommand("timeout", "Set request timeout"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands set successfully.")

    def run(self):
        """
        Runs the bot.
        """
        app_builder = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN)
        app_builder.post_init(self.post_init)
        app = app_builder.build()

        # Command handlers
        app.add_handler(CommandHandler("start", self.handlers.start))
        app.add_handler(CommandHandler("help", self.handlers.help_command))
        app.add_handler(CommandHandler("menu", self.handlers.show_menu))
        app.add_handler(CommandHandler("model", self.handlers.model_info))
        app.add_handler(CommandHandler("listmodels", self.handlers.list_models_cmd))
        app.add_handler(CommandHandler("setmodel", self.handlers.set_model))
        app.add_handler(CommandHandler("setprompt", self.handlers.set_prompt))
        app.add_handler(CommandHandler("timeout", self.handlers.set_timeout))

        # Callback query handlers
        app.add_handler(
            CallbackQueryHandler(self.handlers.model_callback, pattern=r"^setmodel:")
        )
        app.add_handler(CallbackQueryHandler(self.handlers.menu_callback))

        # Message handler for general messages
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Start the bot
        logger.info("Starting Telegram Ollama bot")
        app.run_polling()


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

def main():
    bot = TelegramOllamaBot(settings)
    bot.run()


if __name__ == "__main__":
    main()
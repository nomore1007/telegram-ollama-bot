"""Main Telegram Ollama Bot application"""

import logging
import asyncio
import re
import sys
import os

# Load settings using the settings manager
from settings_manager import settings_manager, settings, config



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
from llm_client import LLMClient, OllamaProvider
from summarizers import NewsSummarizer, YouTubeSummarizer
from handlers import TelegramHandlers
from conversation import ConversationManager
from security import InputValidator, RateLimiter
from admin import AdminManager
from personality import Personality, personality_manager
from plugins import plugin_manager
from plugins.telegram_plugin import TelegramPlugin
from plugins.web_search_plugin import WebSearchPlugin
from plugins.discord_plugin import DiscordPlugin
from plugins.weather_plugin import WeatherPlugin
from database import ChannelSettings


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
        # Initialize LLM client based on provider
        llm_provider = getattr(config, 'LLM_PROVIDER', 'ollama')
        llm_kwargs = {
            'model': getattr(config, 'OLLAMA_MODEL', 'llama2'),
            'timeout': getattr(config, 'TIMEOUT', 30)
        }

        if llm_provider == 'ollama':
            llm_kwargs['host'] = getattr(config, 'OLLAMA_HOST', 'http://localhost:11434')
        elif llm_provider in ['openai', 'groq', 'together', 'huggingface', 'anthropic']:
            api_key = getattr(config, f'{llm_provider.upper()}_API_KEY', None)
            if api_key:
                llm_kwargs['api_key'] = api_key
            else:
                logger.warning(f"No API key for {llm_provider}, falling back to ollama")
                llm_provider = 'ollama'
                llm_kwargs['host'] = getattr(config, 'OLLAMA_HOST', 'http://localhost:11434')

        self.llm = LLMClient(provider=llm_provider, **llm_kwargs)
        self.news_summarizer = NewsSummarizer(self.llm)
        self.youtube_summarizer = YouTubeSummarizer(self.llm)
        self.conversation_manager = ConversationManager()
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()
        self.custom_prompt = getattr(config, 'DEFAULT_PROMPT', "You are a helpful AI assistant.")
        self.bot_username = None
        self.admin_manager = AdminManager(getattr(config, 'ADMIN_USER_IDS', []))
        self.channel_settings = {}  # In-memory cache for per-channel settings

        # Initialize database
        self._init_database()

        # Load persisted channel settings
        self._load_channel_settings()

        personality_name = getattr(config, 'DEFAULT_PERSONALITY', 'helpful')
        try:
            self.personality = Personality(personality_name)
        except ValueError:
            logger.warning(f"Invalid personality '{personality_name}', using 'helpful'")
            self.personality = Personality.HELPFUL

        # Initialize plugins
        self._load_plugins()

        # Legacy handlers for backward compatibility
        self.handlers = TelegramHandlers(self)

    def _init_database(self):
        """Initialize database connection and create tables."""
        from database import Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Use SQLite for simplicity - can be changed to PostgreSQL/MySQL later
        database_url = self.config.get('DATABASE_URL', 'sqlite:///deepthought_bot.db')
        self.db_engine = create_engine(database_url, echo=False)
        self.db_session = sessionmaker(bind=self.db_engine)

        # Create tables
        Base.metadata.create_all(self.db_engine)
        logger.info("Database initialized")

    def _load_channel_settings(self):
        """Load channel settings from database."""
        session = self.db_session()
        try:
            settings = session.query(ChannelSettings).all()
            for setting in settings:
                self.channel_settings[setting.channel_id] = {
                    'provider': setting.provider,
                    'model': setting.model,
                    'host': setting.host,
                    'prompt': setting.prompt
                }
            logger.info(f"Loaded {len(settings)} channel settings from database")
        except Exception as e:
            logger.error(f"Error loading channel settings: {e}")
        finally:
            session.close()

    def save_channel_setting(self, channel_id: str, key: str, value):
        """Save a channel setting to database and memory cache."""
        session = self.db_session()
        try:
            # Get or create channel settings record
            channel_setting = session.query(ChannelSettings).filter_by(channel_id=channel_id).first()
            if not channel_setting:
                channel_setting = ChannelSettings(channel_id=channel_id)
                session.add(channel_setting)

            # Update the setting
            setattr(channel_setting, key, value)
            session.commit()

            # Update in-memory cache
            if channel_id not in self.channel_settings:
                self.channel_settings[channel_id] = {}
            self.channel_settings[channel_id][key] = value

            logger.debug(f"Saved channel setting {channel_id}.{key} = {value}")

        except Exception as e:
            logger.error(f"Error saving channel setting: {e}")
            session.rollback()
        finally:
            session.close()

    def get_channel_setting(self, channel_id: str, key: str, default=None):
        """Get a channel setting, falling back to global default if not set."""
        channel_settings = self.channel_settings.get(channel_id, {})

        # If channel has the setting, return it
        if key in channel_settings and channel_settings[key] is not None:
            return channel_settings[key]

        # Otherwise return global default
        if key == 'provider':
            return 'ollama'
        elif key == 'model':
            return self.config.OLLAMA_MODEL
        elif key == 'host':
            return self.config.OLLAMA_HOST
        elif key == 'prompt':
            return self.custom_prompt

        return default

    def _load_plugins(self):
        """Load and initialize plugins."""
        enabled_plugins = getattr(self.config, 'ENABLED_PLUGINS', [])

        # Load available plugins with their configs
        plugin_configs = getattr(self.config, 'PLUGINS', {})
        plugin_manager.load_plugin("telegram", TelegramPlugin, plugin_configs.get('telegram', {}))
        plugin_manager.load_plugin("web_search", WebSearchPlugin, plugin_configs.get('web_search', {}))
        plugin_manager.load_plugin("discord", DiscordPlugin, plugin_configs.get('discord', {}))
        plugin_manager.load_plugin("weather", WeatherPlugin, plugin_configs.get('weather', {}))

        # Filter enabled plugins based on configuration requirements
        filtered_plugins = []
        for plugin_name in enabled_plugins:
            if plugin_name == 'telegram':
                config = plugin_configs.get('telegram', {})
                bot_token = config.get('bot_token') if config else getattr(self.config, 'TELEGRAM_BOT_TOKEN', None)
                if not bot_token or (isinstance(bot_token, str) and bot_token.startswith('YOUR_') and bot_token.endswith('_HERE')):
                    logger.warning(f"Telegram plugin disabled: bot_token not configured")
                    continue
            elif plugin_name == 'discord':
                config = plugin_configs.get('discord', {})
                if not config.get('bot_token'):
                    logger.warning(f"Discord plugin disabled: bot_token not configured")
                    continue
            # Web search doesn't require tokens
            filtered_plugins.append(plugin_name)

        # Enable only plugins with valid configuration
        for plugin_name in filtered_plugins:
            plugin_manager.enable_plugin(plugin_name)

        # Enable configured plugins
        for plugin_name in enabled_plugins:
            if plugin_name.strip() in plugin_manager.plugins:
                plugin_manager.enable_plugin(plugin_name.strip())

        # Initialize all enabled plugins
        plugin_manager.initialize_plugins(self)

    # ---------------------------------------------------------------
    # Message handling
    # ---------------------------------------------------------------

    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle incoming messages"""
        if update.message:
            message_text = update.message.text
            if not message_text:
                return



            # SECURITY: Add message size limits
            MAX_MESSAGE_SIZE = 4096  # characters
            if len(message_text) > MAX_MESSAGE_SIZE:
                await update.message.reply_text("🚫 Message too long. Please keep messages under 4000 characters.")
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

            logger.info(f"Message in {chat_type} chat, bot_username: {self.bot_username}")

            if is_group_chat:
                logger.info(f"Group chat message: '{message_text}', checking for mention")
                if self.bot_username and f"@{self.bot_username}" in message_text:
                    bot_mentioned = True
                    logger.info(f"Bot mentioned, processing message")
                    # Remove bot mention from the message text
                    message_text = message_text.replace(f"@{self.bot_username}", "").strip()
                    # Remove any leading/trailing whitespace after removing mention
                    message_text = message_text.strip()
                else:
                    logger.info(f"Bot not mentioned in group chat, ignoring")
                    # If in group chat and bot not mentioned, ignore
                    return

            # If not a group chat or bot was mentioned in a group chat
            # Process the message with AI
            logger.info("Sending message to AI for processing")

            # Send thinking message
            thinking_message = await update.message.reply_text("🤔 Thinking…")

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
                        logger.error(f"Error processing video {url}: {type(e).__name__}")
                        await update.message.reply_text(f"❌ Failed to process video. Please try again later.")

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
                        logger.error(f"Error processing article {url}: {type(e).__name__}")
                        await update.message.reply_text(f"❌ Failed to process article. Please try again later.")

                return

            # Regular chat message with conversation context
            thinking_message = await update.message.reply_text("🤔 Thinking…")

            # Add user message to conversation history
            chat_id = update.message.chat.id
            self.conversation_manager.add_user_message(chat_id, message_text)

            # Get per-channel settings using the same method as other commands
            channel_id_str = str(chat_id)
            channel_model = self.get_channel_setting(channel_id_str, 'model')
            channel_prompt = self.get_channel_setting(channel_id_str, 'prompt') or self.custom_prompt
            channel_provider = self.get_channel_setting(channel_id_str, 'provider')
            channel_host = self.get_channel_setting(channel_id_str, 'host') if channel_provider == 'ollama' else None



            # Get API key for the provider
            api_key = None
            if channel_provider != 'ollama':
                api_key_env = f'{channel_provider.upper()}_API_KEY'
                api_key = getattr(self.config, api_key_env, None)

            # Create LLM client for this channel's provider
            from llm_client import LLMClient
            channel_llm = LLMClient(
                provider=channel_provider,
                model=channel_model,
                host=channel_host,
                api_key=api_key
            )

            # Get conversation context
            # Build prompt with personality
            personality_prompt = personality_manager.get_system_prompt(self.personality, channel_prompt)
            context = self.conversation_manager.get_context(chat_id, personality_prompt)

            # Generate response with full context
            response = await channel_llm.generate(context)

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
            BotCommand("changemodel", "Change AI model"),
            BotCommand("setprompt", "Set custom AI prompt"),
            BotCommand("timeout", "Set request timeout"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands set successfully.")

        # Start background task to check for settings changes
        asyncio.create_task(self._check_settings_changes())

    async def _check_settings_changes(self):
        """Periodically check for settings file changes."""
        import os
        settings_file = os.path.join(os.path.dirname(__file__), 'settings.py')
        last_mtime = os.path.getmtime(settings_file) if os.path.exists(settings_file) else 0

        while True:
            await asyncio.sleep(60)  # Check every minute
            try:
                current_mtime = os.path.getmtime(settings_file) if os.path.exists(settings_file) else 0
                if current_mtime > last_mtime:
                    logger.info("Settings file has been modified. Some changes may require a bot restart to take effect.")
                    last_mtime = current_mtime
            except Exception as e:
                logger.error(f"Error checking settings file: {e}")

    def run(self):
        """
        Runs the bot.
        """
        telegram_config = self.config.PLUGINS.get('telegram', {})
        bot_token = telegram_config.get('bot_token')
        if not bot_token:
            raise ValueError("Telegram bot token not configured in PLUGINS['telegram']['bot_token']")
        app_builder = Application.builder().token(bot_token)
        app_builder.post_init(self.post_init)
        app = app_builder.build()

        # Command handlers from plugins
        for plugin in plugin_manager.get_enabled_plugins():
            for command in plugin.get_commands():
                handler_method = getattr(plugin, f"handle_{command}", None)
                if handler_method:
                    # getattr on instance returns bound method, use directly
                    app.add_handler(CommandHandler(command, handler_method))

        # Legacy command handlers removed - using plugin system exclusively

        # Callback query handlers from plugins
        telegram_plugin = plugin_manager.plugins.get("telegram")
        logger.info(f"Telegram plugin found: {telegram_plugin is not None}")
        logger.info(f"Telegram plugin enabled: {plugin_manager.plugins.get('telegram') in plugin_manager.get_enabled_plugins()}")
        if telegram_plugin and plugin_manager.plugins["telegram"] in plugin_manager.get_enabled_plugins():
            logger.info("Registering callback handlers...")

            app.add_handler(
                CallbackQueryHandler(telegram_plugin.handle_model_callback, pattern=r"^changemodel:")
            )
            app.add_handler(CallbackQueryHandler(telegram_plugin.handle_menu_callback))

            logger.info("Callback handlers registered")
        else:
            logger.error("Telegram plugin not found or not enabled - callback handlers not registered!")

        # Legacy callback handlers removed - using plugin system



        # Message handler for general messages
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Start the bot
        logger.info("Starting Telegram Ollama bot")
        app.run_polling()

    def run_discord_bot(self):
        """Run Discord bot if enabled."""
        discord_plugin = plugin_manager.plugins.get("discord")
        if discord_plugin and plugin_manager.plugins["discord"] in plugin_manager.get_enabled_plugins():
            discord_config = self.config.PLUGINS.get('discord', {})
            discord_token = discord_config.get('bot_token')
            if discord_token:
                logger.info("Starting Discord bot")
                discord_plugin.run_discord_bot(discord_token)
            else:
                logger.warning("Discord bot token not configured")


# -------------------------------------------------------------------
# Backward compatibility aliases
# -------------------------------------------------------------------

OllamaClient = LLMClient  # For backward compatibility with tests

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

def main():
    bot = TelegramOllamaBot(settings)

    # Run Discord bot in background if enabled
    import threading
    discord_thread = threading.Thread(target=bot.run_discord_bot)
    discord_thread.daemon = True
    discord_thread.start()

    # Run Telegram bot
    bot.run()


if __name__ == "__main__":
    main()
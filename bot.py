"""Main Telegram Ollama Bot application"""

import logging
import asyncio
import re
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

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
from telegram.request import HTTPXRequest
from constants import (    MAX_MESSAGE_LENGTH, MAX_ARTICLES_PER_MESSAGE, MAX_VIDEOS_PER_MESSAGE,
    LOG_FORMAT, LOG_LEVEL
)

logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, config.LOG_LEVEL),
    force=True, # Force re-configuration of logging for modules loaded earlier
)
logger = logging.getLogger(__name__)

from llm_client import LLMClient, OllamaProvider
from summarizers import NewsSummarizer, YouTubeSummarizer
from handlers import TelegramHandlers
from conversation import ConversationManager
from security import InputValidator, RateLimiter
from admin import AdminManager
from personality import Personality, personality_manager

from plugins import plugin_manager

# Import plugins with graceful error handling
def safe_import_plugin(module_name, class_name):
    """Safely import a plugin class, returning None if import fails"""
    try:
        module = __import__(f'plugins.{module_name}', fromlist=[class_name])
        plugin_class = getattr(module, class_name)
        logger.debug(f"Successfully imported plugin: {module_name}")
        return plugin_class
    except ImportError as e:
        logger.warning(f"Failed to import plugin {module_name}: {e}. Skipping this plugin.")
        return None
    except Exception as e:
        logger.error(f"Error importing plugin {module_name}: {e}. Skipping this plugin.")
        return None

# Import plugins safely - bot will continue even if some plugins fail to load
TelegramPlugin = safe_import_plugin('telegram_plugin', 'TelegramPlugin')
WebSearchPlugin = safe_import_plugin('web_search_plugin', 'WebSearchPlugin')
DiscordPlugin = safe_import_plugin('discord_plugin', 'DiscordPlugin')
WeatherPlugin = safe_import_plugin('weather_plugin', 'WeatherPlugin')
CalculatorPlugin = safe_import_plugin('calculator_plugin', 'CalculatorPlugin')
CurrencyPlugin = safe_import_plugin('currency_plugin', 'CurrencyPlugin')
TranslationPlugin = safe_import_plugin('translation_plugin', 'TranslationPlugin')
TriviaPlugin = safe_import_plugin('trivia_plugin', 'TriviaPlugin')
URLShortenerPlugin = safe_import_plugin('url_shortener_plugin', 'URLShortenerPlugin')
from database import ChannelSettings




# -------------------------------------------------------------------
# Main Bot Class
# -------------------------------------------------------------------

class TelegramOllamaBot:
    """Main Telegram bot class integrating Ollama AI"""

    def __init__(self, config, test_mode: bool = False): # Added test_mode
        self.config = config
        self.test_mode = test_mode # Stored test_mode
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
        config_dir_path = self.config.BOT_CONFIG_DIR
        db_file_path = config_dir_path / 'deepthought_bot.db'
        database_url = self.config.get('DATABASE_URL', f'sqlite:///{db_file_path}')
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

        # Load available plugins with their configs (only if import succeeded)
        plugin_configs = getattr(self.config, 'PLUGINS', {})
        if TelegramPlugin:
            plugin_manager.load_plugin("telegram", TelegramPlugin, plugin_configs.get('telegram', {}))
        if WebSearchPlugin:
            plugin_manager.load_plugin("web_search", WebSearchPlugin, plugin_configs.get('web_search', {}))
        if DiscordPlugin:
            plugin_manager.load_plugin("discord", DiscordPlugin, plugin_configs.get('discord', {}))
        if WeatherPlugin:
            plugin_manager.load_plugin("weather", WeatherPlugin, plugin_configs.get('weather', {}))
        if CalculatorPlugin:
            plugin_manager.load_plugin("calculator", CalculatorPlugin, plugin_configs.get('calculator', {}))
        if CurrencyPlugin:
            plugin_manager.load_plugin("currency", CurrencyPlugin, plugin_configs.get('currency', {}))
        if TranslationPlugin:
            plugin_manager.load_plugin("translation", TranslationPlugin, plugin_configs.get('translation', {}))
        if TriviaPlugin:
            plugin_manager.load_plugin("trivia", TriviaPlugin, plugin_configs.get('trivia', {}))
        if URLShortenerPlugin:
            plugin_manager.load_plugin("url_shortener", URLShortenerPlugin, plugin_configs.get('url_shortener', {}))

        # Filter enabled plugins based on configuration requirements
        # Only include plugins that were successfully imported and loaded
        filtered_plugins = []
        for plugin_name in enabled_plugins:
            if plugin_name not in plugin_manager.plugins:
                logger.warning(f"Skipping plugin '{plugin_name}' - not loaded (import failed)")
                continue

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
        logger.debug(f"handle_message called for chat_id: {update.message.chat.id}")
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

            logger.debug(f"Message in {chat_type} chat, bot_username: {self.bot_username}")

            if is_group_chat:
                logger.debug(f"Group chat message: '{message_text}', checking for mention")
                if self.bot_username and f"@{self.bot_username}" in message_text:
                    bot_mentioned = True
                    logger.debug(f"Bot mentioned, processing message")
                    # Remove bot mention from the message text
                    message_text = message_text.replace(f"@{self.bot_username}", "").strip()
                    # Remove any leading/trailing whitespace after removing mention
                    message_text = message_text.strip()
                else:
                    logger.debug(f"Bot not mentioned in group chat, ignoring")
                    # If in group chat and bot not mentioned, ignore
                    return

            # Check if this is an answer to a trivia question
            trivia_handled = await self._check_trivia_answer(update, context)
            if trivia_handled:
                return

            # If not a group chat or bot was mentioned in a group chat
            # Process the message with AI
            logger.debug("Sending message to AI for processing")

            # Check for YouTube URLs first (highest priority)
            youtube_urls = self.youtube_summarizer.extract_video_urls(message_text)

            if youtube_urls:
                try:
                    await update.message.reply_text("🎬 *YouTube video detected! Summarizing...*", parse_mode="Markdown")
                except Exception as e:
                    logger.warning(f"Failed to send YouTube detection message: {type(e).__name__}")
                    return

                for url in youtube_urls[:MAX_VIDEOS_PER_MESSAGE]:  # Limit videos per message
                    try:
                        # Send processing message with timeout protection
                        try:
                            await asyncio.wait_for(
                                update.message.reply_text("⏳ Processing video..."),
                                timeout=5.0
                            )
                        except asyncio.TimeoutError:
                            logger.warning("Timeout sending video processing message")
                            continue
                        except Exception as e:
                            logger.warning(f"Failed to send video processing message: {type(e).__name__}")
                            continue

                        # Process video with timeout
                        try:
                            summary = await asyncio.wait_for(
                                self.youtube_summarizer.process_video(url),
                                timeout=120.0  # 2 minutes for video processing
                            )
                        except asyncio.TimeoutError:
                            await update.message.reply_text("⏳ Video processing timed out. Please try again.")
                            continue

                        # Send summary with timeout protection
                        try:
                            # Validate summary before sending
                            if not summary or len(summary.strip()) == 0:
                                await update.message.reply_text("❌ Failed to generate video summary.")
                                continue

                            if len(summary) > MAX_MESSAGE_LENGTH:
                                parts = [summary[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(summary), MAX_MESSAGE_LENGTH)]
                                for i, part in enumerate(parts):
                                    await asyncio.wait_for(
                                        update.message.reply_text(part, parse_mode="Markdown", disable_web_page_preview=i>0),
                                        timeout=10.0
                                    )
                            else:
                                await asyncio.wait_for(
                                    update.message.reply_text(summary, parse_mode="Markdown"),
                                    timeout=10.0
                                )
                        except asyncio.TimeoutError:
                            logger.warning("Timeout sending video summary")
                            try:
                                await update.message.reply_text("⏳ Summary is ready but took too long to send.")
                            except:
                                pass
                        except Exception as e:
                            logger.warning(f"Failed to send video summary: {type(e).__name__}")
                            try:
                                await update.message.reply_text("❌ Failed to send video summary.")
                            except:
                                pass

                    except Exception as e:
                        logger.error(f"Error processing video {url}: {type(e).__name__}")
                        try:
                            await asyncio.wait_for(
                                update.message.reply_text("❌ Failed to process video. Please try again later."),
                                timeout=5.0
                            )
                        except:
                            logger.warning("Failed to send video error message")

                return

            # Check for news URLs second
            news_urls = self.news_summarizer.extract_urls(message_text)

            if news_urls:
                try:
                    await asyncio.wait_for(
                        update.message.reply_text("📰 *News article detected! Summarizing...*", parse_mode="Markdown"),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Timeout sending article detection message")
                    return
                except Exception as e:
                    logger.warning(f"Failed to send article detection message: {type(e).__name__}")
                    return

                for url in news_urls[:MAX_ARTICLES_PER_MESSAGE]:  # Limit articles per message
                    try:
                        # Send processing message with timeout protection
                        try:
                            await asyncio.wait_for(
                                update.message.reply_text("⏳ Processing article..."),
                                timeout=5.0
                            )
                        except asyncio.TimeoutError:
                            logger.warning("Timeout sending article processing message")
                            continue
                        except Exception as e:
                            logger.warning(f"Failed to send article processing message: {type(e).__name__}")
                            continue

                        # Process article with timeout
                        try:
                            summary = await asyncio.wait_for(
                                self.news_summarizer.process_article(url),
                                timeout=90.0  # 90 seconds for article processing
                            )
                        except asyncio.TimeoutError:
                            try:
                                await asyncio.wait_for(
                                    update.message.reply_text("⏳ Article processing timed out. Please try again."),
                                    timeout=5.0
                                )
                            except:
                                logger.warning("Failed to send article timeout message")
                            continue

                        # Send summary with timeout protection
                        try:
                            if len(summary) > MAX_MESSAGE_LENGTH:
                                parts = [summary[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(summary), MAX_MESSAGE_LENGTH)]
                                for i, part in enumerate(parts):
                                    await asyncio.wait_for(
                                        update.message.reply_text(part, parse_mode="Markdown", disable_web_page_preview=i>0),
                                        timeout=10.0
                                    )
                            else:
                                await asyncio.wait_for(
                                    update.message.reply_text(summary, parse_mode="Markdown"),
                                    timeout=10.0
                                )
                        except asyncio.TimeoutError:
                            logger.warning("Timeout sending article summary")
                        except Exception as e:
                            logger.warning(f"Failed to send article summary: {type(e).__name__}")

                    except Exception as e:
                        logger.error(f"Error processing article {url}: {type(e).__name__}")
                        # Try to get more specific error from summarizer
                        try:
                            article_data = await self.news_summarizer.extract_article_content(url)
                            if not article_data["success"]:
                                error_msg = article_data.get("error", "Unknown error")
                                try:
                                    await asyncio.wait_for(
                                        update.message.reply_text(f"❌ Failed to process article: {error_msg}"),
                                        timeout=5.0
                                    )
                                except:
                                    logger.warning("Failed to send article error message")
                            else:
                                try:
                                    await asyncio.wait_for(
                                        update.message.reply_text("❌ Failed to summarize article. Please try again later."),
                                        timeout=5.0
                                    )
                                except:
                                    logger.warning("Failed to send article summary error message")
                        except Exception as inner_e:
                            logger.error(f"Error getting article error details: {type(inner_e).__name__}")
                            try:
                                await asyncio.wait_for(
                                    update.message.reply_text("❌ Failed to process article. Please try again later."),
                                    timeout=5.0
                                )
                            except:
                                logger.warning("Failed to send generic article error message")

                return

            # Regular chat message with conversation context
            # Send thinking message with timeout protection
            try:
                thinking_message = await asyncio.wait_for(
                    update.message.reply_text("🤔 Thinking…"),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout sending thinking message")
                return
            except Exception as e:
                logger.warning(f"Failed to send thinking message: {type(e).__name__}")
                return

            # Add user message to conversation history
            chat_id = update.message.chat.id
            self.conversation_manager.add_user_message(chat_id, message_text)

            # Get per-channel settings using the same method as other commands
            channel_id_str = str(chat_id)
            channel_model = self.get_channel_setting(channel_id_str, 'model')
            channel_prompt = self.get_channel_setting(channel_id_str, 'prompt') or self.custom_prompt
            channel_provider = self.get_channel_setting(channel_id_str, 'provider') or 'ollama'  # Default to ollama
            channel_host = self.get_channel_setting(channel_id_str, 'host') if channel_provider == 'ollama' else None

            # Debug: Check what get_channel_setting returns
            raw_provider = self.get_channel_setting(channel_id_str, 'provider')
            raw_host = self.get_channel_setting(channel_id_str, 'host')
            logger.debug(f"Channel {channel_id_str}: raw_provider={raw_provider}, raw_host={raw_host}, final_provider={channel_provider}, final_host={channel_host}")



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
            logger.debug(f"LLM Context for chat {chat_id}: {context}")

            # Get available tools
            tools = self._get_available_tools()

            # Generate response with tool support
            response, tool_calls = await channel_llm.generate_with_tools(context, tools)
            if tool_calls:
                logger.debug(f"LLM generated tool calls for chat {chat_id}: {tool_calls}")

            # Execute tool calls if any
            if tool_calls:
                tool_results = await self._execute_tool_calls(tool_calls)

                # Generate final response with tool results
                if tool_results:
                    context_with_tools = f"{context}\n\nTool Results:\n{tool_results}\n\nPlease provide your final answer based on these results."
                    response = await channel_llm.generate(context_with_tools)

            # Add assistant response to conversation history
            self.conversation_manager.add_assistant_message(chat_id, response)

            # Send response with timeout protection
            try:
                await asyncio.wait_for(
                    thinking_message.edit_text(response),
                    timeout=15.0  # 15 seconds for response
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout editing thinking message with response")
                # Try to send as new message instead
                try:
                    await asyncio.wait_for(
                        update.message.reply_text(response),
                        timeout=15.0
                    )
                except asyncio.TimeoutError:
                    logger.error("Timeout sending response message")
                except Exception as e:
                    logger.error(f"Failed to send response message: {type(e).__name__}")
            except Exception as e:
                logger.error(f"Failed to edit thinking message: {type(e).__name__}")
                # Try to send as new message instead
                try:
                    await asyncio.wait_for(
                        update.message.reply_text(response),
                        timeout=15.0
                    )
                except Exception as inner_e:
                    logger.error(f"Failed to send fallback response message: {type(inner_e).__name__}")

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



    def _is_valid_telegram_token(self, token: Optional[str]) -> bool:
        """Checks if a Telegram bot token is valid (not None, not empty, not a placeholder)."""
        if not token:
            return False
        if isinstance(token, str) and (
            token.strip() == "" or
            token.startswith('YOUR_') and token.endswith('_HERE') or
            token == "12345:ABCDEF" # Add check for the specific dummy token
        ):
            return False
        return True

    async def _test_initialize_and_run(self, app: Application):
        """Initializes the application for testing purposes and then runs the polling."""
        try:
            logger.info("Test mode: Attempting to initialize Telegram API connection...")
            await app.initialize() # This calls self.bot.get_me()
            logger.info("Test mode: Telegram API connection successful.")
            logger.info("Test mode: Initializing plugins for test run...")
            # We explicitly call post_init here as run_polling() won't be called
            await self.post_init(app) # Ensure commands are set
            logger.info("Test mode: Application initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Test mode: Telegram API connection failed: {e}")
            return False

    def run(self):
        """
        Runs the bot.
        """
        telegram_bot_active = False
        discord_bot_active = False
        app = None # Initialize app to None

        # --- Telegram Bot Setup ---
        telegram_config = self.config.PLUGINS.get('telegram', {})
        bot_token = telegram_config.get('bot_token')

        if self._is_valid_telegram_token(bot_token):
            telegram_api_timeout = getattr(self.config, 'TELEGRAM_API_TIMEOUT', 300.0)
            request = HTTPXRequest(connect_timeout=telegram_api_timeout, read_timeout=telegram_api_timeout)
            app_builder = Application.builder().token(bot_token).request(request)
            app_builder.post_init(self.post_init)
            app = app_builder.build()
            telegram_bot_active = True
            logger.info("Telegram bot is configured and will attempt to start.")

            # Command handlers from plugins
            for plugin in plugin_manager.get_enabled_plugins():
                for command in plugin.get_commands():
                    handler_method = getattr(plugin, f"handle_{command}", None)
                    if handler_method:
                        app.add_handler(CommandHandler(command, handler_method))

            # Callback query handlers from plugins
            telegram_plugin = plugin_manager.plugins.get("telegram")
            logger.info(f"Telegram plugin found: {telegram_plugin is not None}")
            logger.info(f"Telegram plugin enabled: {plugin_manager.plugins.get('telegram') in plugin_manager.get_enabled_plugins()}")
            if telegram_plugin and plugin_manager.plugins["telegram"] in plugin_manager.get_enabled_plugins():
                logger.info("Registering callback handlers...")
                app.add_handler(CallbackQueryHandler(telegram_plugin.handle_model_callback, pattern=r"^changemodel:"))
                app.add_handler(CallbackQueryHandler(telegram_plugin.handle_menu_callback))
                logger.info("Callback handlers registered")
            else:
                logger.error("Telegram plugin not found or not enabled - callback handlers not registered!")

            # Message handler for general messages
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        else:
            logger.warning("Telegram bot token is invalid or not configured. Telegram bot will not be started.")
            # app remains None

        # --- Discord Bot Setup (moved from main() to run() for consistent active check) ---
        discord_plugin = plugin_manager.plugins.get("discord")
        if discord_plugin and plugin_manager.plugins["discord"] in plugin_manager.get_enabled_plugins():
            discord_config = self.config.PLUGINS.get('discord', {})
            discord_token = discord_config.get('bot_token')
            if discord_token:
                logger.info("Discord bot is configured and will attempt to start.")
                discord_bot_active = True
            else:
                logger.warning("Discord bot token not configured. Discord bot will not be started.")
        
        # --- Overall Connection Status Check ---
        if not telegram_bot_active and not discord_bot_active:
            logger.error("No bot connections (Telegram or Discord) are active. Please check your configuration.")
            if self.test_mode:
                logger.info("Test mode completed with no active connections.")
            return # Exit if no connections are active

        # If we are in test mode and Telegram bot is active, run the test initialization
        if self.test_mode:
            if telegram_bot_active:
                logger.info("Running Telegram bot in test mode (initialization and API connection test).")
                asyncio.run(self._test_initialize_and_run(app)) # Call the async test initializer
            else:
                logger.info("Test mode completed without Telegram bot active.")
            return # Exit after initialization test

        # --- Start Discord Bot in Background (only if configured) ---
        if discord_bot_active:
            import threading
            # Call the actual run_discord_bot method which handles starting the thread
            threading.Thread(target=self.run_discord_bot).start()
            logger.info("Discord bot background thread started.")

        # --- Start Telegram Bot (only if configured and not in test mode) ---
        if telegram_bot_active:
            logger.info("Starting Telegram Ollama bot")
            logger.debug("Attempting to run Telegram polling...")
            app.run_polling()
            logger.debug("Telegram polling has stopped.")

    def _get_available_tools(self) -> list:
        """Get list of available tools for the LLM"""
        tools = []

        # Web search tool
        if 'web_search' in plugin_manager.plugins and plugin_manager.plugins['web_search'] in plugin_manager.get_enabled_plugins():
            tools.append({
                'name': 'web_search',
                'description': 'Search the web for current information and answer questions',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'The search query or question to answer'
                    }
                }
            })

        # Weather tool
        if 'weather' in plugin_manager.plugins and plugin_manager.plugins['weather'] in plugin_manager.get_enabled_plugins():
            tools.append({
                'name': 'weather',
                'description': 'Get current weather and forecast for a location',
                'parameters': {
                    'location': {
                        'type': 'string',
                        'description': 'City name or location'
                    }
                }
            })

        # Calculator tool
        if 'calculator' in plugin_manager.plugins and plugin_manager.plugins['calculator'] in plugin_manager.get_enabled_plugins():
            tools.append({
                'name': 'calculator',
                'description': 'Evaluate mathematical expressions and solve calculations',
                'parameters': {
                    'expression': {
                        'type': 'string',
                        'description': 'Mathematical expression to evaluate (e.g., "2+2*3", "sqrt(16)")'
                    }
                }
            })

        # Currency converter tool
        if 'currency' in plugin_manager.plugins and plugin_manager.plugins['currency'] in plugin_manager.get_enabled_plugins():
            tools.append({
                'name': 'currency_convert',
                'description': 'Convert between different currencies',
                'parameters': {
                    'amount': {
                        'type': 'number',
                        'description': 'Amount to convert'
                    },
                    'from_currency': {
                        'type': 'string',
                        'description': 'Source currency code (e.g., USD, EUR, GBP)'
                    },
                    'to_currency': {
                        'type': 'string',
                        'description': 'Target currency code (e.g., USD, EUR, GBP)'
                    }
                }
            })

        # Translation tool
        if 'translation' in plugin_manager.plugins and plugin_manager.plugins['translation'] in plugin_manager.get_enabled_plugins():
            tools.append({
                'name': 'translate',
                'description': 'Translate text between languages',
                'parameters': {
                    'text': {
                        'type': 'string',
                        'description': 'Text to translate'
                    },
                    'target_language': {
                        'type': 'string',
                        'description': 'Target language code (e.g., es, fr, de, ja)'
                    },
                    'source_language': {
                        'type': 'string',
                        'description': 'Source language code (optional, auto-detect if not provided)'
                    }
                }
            })

        return tools

    async def _execute_tool_calls(self, tool_calls: list) -> str:
        """Execute tool calls and return formatted results"""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get('tool')
            parameters = tool_call.get('parameters', {})

            try:
                result = await self._execute_single_tool(tool_name, parameters)
                results.append(f"Tool: {tool_name}\nResult: {result}")
            except Exception as e:
                results.append(f"Tool: {tool_name}\nError: {str(e)}")

        return "\n\n".join(results)

    async def _execute_single_tool(self, tool_name: str, parameters: dict) -> str:
        logger.debug(f"Executing tool: {tool_name} with parameters: {parameters}")
        """Execute a single tool call"""
        if tool_name == 'web_search':
            query = parameters.get('query', '')
            if not query:
                return "Error: No search query provided"

            # Use web search plugin
            web_plugin = plugin_manager.plugins.get('web_search')
            if web_plugin:
                # Simulate a message update for the plugin
                class MockMessage:
                    def __init__(self, text):
                        self.text = text

                class MockUpdate:
                    def __init__(self, message):
                        self.message = message

                # This is a simplified approach - in practice, you'd need to properly mock the update
                # For now, return a placeholder
                return f"Web search results for: {query} (simulated)"

        elif tool_name == 'weather':
            location = parameters.get('location', '')
            if not location:
                return "Error: No location provided"

            weather_plugin = plugin_manager.plugins.get('weather')
            if weather_plugin:
                # This would need proper implementation
                return f"Weather for {location}: Sunny, 72°F (simulated)"

        elif tool_name == 'calculator':
            expression = parameters.get('expression', '')
            if not expression:
                return "Error: No expression provided"

            calc_plugin = plugin_manager.plugins.get('calculator')
            if calc_plugin:
                # For this test, we can directly call the plugin's _safe_eval if it's sync
                # For async, we'd mock it or run it in a sync wrapper
                try:
                    # Assuming _safe_eval is synchronous
                    # If it's async, we'd need to await it and potentially mock aiohttp calls within it
                    result = calc_plugin._safe_eval(expression)
                    return f"Result: {result}"
                except Exception as e:
                    return f"Calculation error: {e}"

        elif tool_name == 'currency_convert':
            amount = parameters.get('amount', 0)
            from_currency = parameters.get('from_currency', '').upper()
            to_currency = parameters.get('to_currency', '').upper()

            if not amount or not from_currency or not to_currency:
                return "Error: Missing required parameters"

            currency_plugin = plugin_manager.plugins.get('currency')
            if currency_plugin:
                # This would need proper implementation
                return f"Converted {amount} {from_currency} to approximately {amount * 1.1} {to_currency} (simulated)"

        elif tool_name == 'translate':
            text = parameters.get('text', '')
            target_lang = parameters.get('target_language', '')
            source_lang = parameters.get('source_language')

            if not text or not target_lang:
                return "Error: Missing required parameters"

            translation_plugin = plugin_manager.plugins.get('translation')
            if translation_plugin:
                # This would need proper implementation
                return f"Translated '{text}' to {target_lang}: [translated text] (simulated)"

        return f"Unknown tool: {tool_name}"

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

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check of the bot and its components"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        # Check database
        try:
            # Simple database check
            health_status['components']['database'] = 'healthy'
        except Exception as e:
            health_status['components']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'

        # Check LLM client
        try:
            if hasattr(self, 'llm') and self.llm:
                health_status['components']['llm'] = 'healthy'
            else:
                health_status['components']['llm'] = 'unhealthy: LLM client not initialized'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['components']['llm'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'

        # Check plugins
        enabled_plugins = plugin_manager.get_enabled_plugins()
        health_status['components']['plugins'] = {
            'total': len(enabled_plugins),
            'enabled': [p.name for p in enabled_plugins]
        }

        return health_status

    async def _check_trivia_answer(self, update, context):
        """Check if the message is an answer to a trivia question"""
        if not update.message or not update.message.text:
            return False

        if context.user_data is None:
            return False

        # Check if there's an active quiz or single question
        quiz_active = context.user_data.get('quiz_active', False)
        current_question = context.user_data.get('current_question')

        if not (quiz_active or current_question):
            return False

        # Get trivia plugin
        trivia_plugin = plugin_manager.plugins.get('trivia')
        if not trivia_plugin or trivia_plugin not in plugin_manager.get_enabled_plugins():
            return False

        # Type check for TriviaPlugin
        if not hasattr(trivia_plugin, 'ask_next_question'):
            return False

        user_answer = update.message.text.strip().lower()
        correct_answer = current_question['answer'].strip().lower()

        # Simple answer matching (could be improved with fuzzy matching)
        is_correct = user_answer == correct_answer

        # Clear the current question
        context.user_data['current_question'] = None

        if quiz_active:
            # Update score
            if is_correct:
                context.user_data['quiz_score'] = context.user_data.get('quiz_score', 0) + 1

            score = context.user_data.get('quiz_score', 0)
            questions = context.user_data.get('quiz_questions', 0)

            result_emoji = "✅" if is_correct else "❌"
            correct_text = f"**{current_question['answer']}**" if not is_correct else ""

            await update.message.reply_text(
                f"{result_emoji} {correct_text}\n"
                f"📊 Score: {score}/{questions}\n\n",
                parse_mode="Markdown"
            )

            # Ask next question after a short delay
            import asyncio
            await asyncio.sleep(1)  # Brief pause
            ask_next = getattr(trivia_plugin, 'ask_next_question', None)
            if ask_next:
                await ask_next(update, context)
        else:
            # Single question response
            result_emoji = "✅" if is_correct else "❌"
            correct_text = f"**{current_question['answer']}**" if not is_correct else ""

            await update.message.reply_text(
                f"{result_emoji} {correct_text}\n\n"
                f"Want another question? Use `/question`!\n"
                f"Or start a quiz with `/trivia`!",
                parse_mode="Markdown"
            )

        return True  # Message was handled by trivia


# -------------------------------------------------------------------
# Backward compatibility aliases
# -------------------------------------------------------------------

OllamaClient = LLMClient  # For backward compatibility with tests

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

def main(test_mode: bool = False): # Added test_mode argument
    bot = TelegramOllamaBot(settings, test_mode=test_mode) # Pass test_mode

    # If in test mode, only run initialization and then exit
    if test_mode:
        logger.info("Running bot in test mode (initialization and API connection test).")
        bot.run() # The run method handles the test_mode logic internally
        logger.info("Test mode completed.")
        return

    # Run Telegram bot
    bot.run()


if __name__ == "__main__":
    main()
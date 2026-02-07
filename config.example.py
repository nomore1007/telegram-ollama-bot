# config.example.py
#
# This file serves as an example for the main configuration of the Deepthought Bot.
# To customize your bot, copy this file to `config.py` and modify the values.
#
# IMPORTANT:
# 1. Never commit `config.py` to version control as it may contain sensitive information.
# 2. Environment variables will always override values defined in `config.py`.
# 3. If `config.py` is not found, the bot will create it from this example.

import os
from typing import Optional, List, Dict, Any

# ===========================================
# Core Bot Configuration
# = =========================================

# Bot identity and behavior
BOT_USERNAME: Optional[str] = "DeepthoughtBot"  # Displayed bot username
DEFAULT_PERSONALITY: str = "helpful"  # Options: friendly, professional, humorous, helpful, creative, concise
DEFAULT_PROMPT: str = "You are a helpful AI assistant. Be informative, accurate, and friendly in your responses."

# Admin User IDs (Telegram user IDs of bot administrators)
# Example: [123456789, 987654321]
# For initial setup, you can leave this empty and use `python admin_cli.py setup YOUR_USER_ID`
ADMIN_USER_IDS: List[int] = []

# ===========================================
# LLM Provider Configuration
# ===========================================

# AI provider selection
# Options: ollama, openai, groq, together, huggingface, anthropic
LLM_PROVIDER: str = "ollama"

# Ollama server configuration (only if LLM_PROVIDER is 'ollama')
OLLAMA_HOST: str = "http://localhost:11434"
OLLAMA_MODEL: str = "smollm2:135m" # Default Ollama model to use

# API Keys for cloud providers (leave as None if not using, or if configured via environment variable)
OPENAI_API_KEY: Optional[str] = None
GROQ_API_KEY: Optional[str] = None
TOGETHER_API_KEY: Optional[str] = None
HUGGINGFACE_API_KEY: Optional[str] = None
ANTHROPIC_API_KEY: Optional[str] = None
OPENWEATHERMAP_API_KEY: Optional[str] = None # Required for weather plugin

# AI model parameters
MAX_TOKENS: int = 2000
TEMPERATURE: float = 0.7
TIMEOUT: int = 30 # Request timeout in seconds

# ===========================================
# Plugin Configuration
# ===========================================

# List of enabled plugins.
# Ensure all plugins listed here are correctly configured below.
# Available plugins (modules in the 'plugins' directory):
# telegram, web_search, discord, weather, calculator, currency, translation, trivia, url_shortener
ENABLED_PLUGINS: List[str] = ["telegram", "web_search", "discord", "weather", "calculator", "currency", "translation", "trivia", "url_shortener"]

# Plugin-specific settings
PLUGINS: Dict[str, Any] = {
    'telegram': {
        'bot_token': "YOUR_TELEGRAM_BOT_TOKEN_HERE", # Get from @BotFather
        # 'webhook_url': "https://your.domain/webhook", # Uncomment and configure for webhook deployment
        # 'webhook_port': 8443,
    },
    'discord': {
        'bot_token': None, # Your Discord bot token if enabling Discord plugin
        # 'command_prefix': '!',
    },
    'web_search': {
        # 'api_key': None, # Optional: For specific paid search APIs
        # 'search_engine': 'google', # Options: google, duckduckgo, brave, etc.
    },
    'weather': {
        'api_key': None, # Get from OpenWeatherMap for full functionality
    },
    'calculator': {
        # No specific settings
    },
    'currency': {
        # No specific settings
    },
    'translation': {
        # 'api_key': None, # Optional: For paid translation APIs (e.g., Google Translate)
    },
    'trivia': {
        # 'questions_per_quiz': 5,
        # 'quiz_timeout': 30, # seconds to answer each question
    },
    'url_shortener': {
        # 'api_key': None, # Optional: For URL shortener services
        # 'default_service': 'tinyurl', # Options: tinyurl, bitly, etc.
    }
}

# ===========================================
# Database Configuration
# ===========================================

# SQLite for simplicity - can be changed to PostgreSQL/MySQL later
# Example for PostgreSQL: "postgresql://user:password@host:port/database"
DATABASE_URL: str = "sqlite:///deepthought_bot.db"

# ===========================================
# Logging Configuration
# ===========================================

LOG_LEVEL: str = "INFO" # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ===========================================
# Content Processing Limits
# ===========================================

MAX_MESSAGE_LENGTH: int = 4096
MAX_ARTICLES_PER_MESSAGE: int = 3
MAX_VIDEOS_PER_MESSAGE: int = 2

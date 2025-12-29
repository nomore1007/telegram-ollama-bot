# Example settings file for Deepthought Bot
# This file contains example/default values for demonstration
#
# IMPORTANT: Copy this file to settings.py and modify the values for your setup
# Never commit settings.py to version control as it contains sensitive information
#
# You can also use environment variables instead of modifying this file

import os
from typing import Optional

# ===========================================
# REQUIRED SETTINGS (MUST BE CONFIGURED)
# ===========================================

# Ollama server configuration (if using Ollama) - Global LLM settings
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")

# ===========================================
# OPTIONAL SETTINGS (WITH SENSIBLE DEFAULTS)
# ===========================================

# Bot identity
BOT_USERNAME: Optional[str] = os.getenv("BOT_USERNAME", "DeepthoughtBot")

# AI model parameters
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))

# Default system prompt for AI responses
DEFAULT_PROMPT: str = os.getenv(
    "DEFAULT_PROMPT",
    "You are a helpful AI assistant. Be informative, accurate, and friendly in your responses."
)

# ===========================================
# PLUGIN CONFIGURATION
# ===========================================

# Enabled plugins (comma-separated list)
# Enable plugins you want to use (all available by default for quick start)
ENABLED_PLUGINS: list = os.getenv("ENABLED_PLUGINS", "telegram,web_search,discord").split(",") if os.getenv("ENABLED_PLUGINS") else ["telegram", "web_search", "discord"]

# ===========================================
# ADMIN CONFIGURATION
# ===========================================

# Admin user IDs (Telegram user IDs of bot administrators)
# Example: [123456789, 987654321]
# Leave empty for initial setup: []
ADMIN_USER_IDS: list = [
    # Add your Telegram user ID here after initial setup
    # You can find your user ID using /userid command after bot is running
]

# ===========================================
# EXTERNAL SERVICE CONFIGURATION
# ===========================================

# Discord Bot Token (optional - only if using Discord)
DISCORD_BOT_TOKEN: Optional[str] = os.getenv("DISCORD_BOT_TOKEN")

# ===========================================
# BOT PERSONALITY CONFIGURATION
# ===========================================

# Default bot personality
# Options: friendly, professional, humorous, helpful, creative, concise
DEFAULT_PERSONALITY: str = os.getenv("DEFAULT_PERSONALITY", "helpful")

# ===========================================
# LLM PROVIDER CONFIGURATION
# ===========================================

# AI provider selection
# Options: ollama, openai, groq, together, huggingface, anthropic
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

# API Keys for cloud providers (leave as None if not using)
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
TOGETHER_API_KEY: Optional[str] = os.getenv("TOGETHER_API_KEY")
HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

# ===========================================
# PLUGIN CONFIGURATIONS
# ===========================================

# Plugin-specific settings
PLUGINS: dict = {
    'telegram': {
        'bot_token': os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE"),
        # Add other telegram-specific settings here
    },
    'discord': {
        'bot_token': os.getenv("DISCORD_BOT_TOKEN"),
        # Add other discord-specific settings here
    },
    'web_search': {
        # Web search specific settings
    }
}

# ===========================================
# SETUP INSTRUCTIONS
# ===========================================
#
# 1. Copy this file to settings.py:
#    cp settings.example.py settings.py
#
# 2. Edit settings.py with your actual values:
#    - Configure PLUGINS dict with your bot tokens and plugin settings
#    - Configure OLLAMA_HOST if using Ollama
#    - Add API keys for cloud providers if needed
#    - Set other options as desired
#
# 3. For initial setup, leave ADMIN_USER_IDS empty
#    Then use: python admin_cli.py setup YOUR_USER_ID
#
# 4. Or set environment variables instead of editing the file
#
# NEVER commit settings.py to version control!
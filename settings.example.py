# Example settings file
# Copy this to settings.py and fill in your actual values
# OR better yet, use environment variables!

import os
from typing import Optional

# Load environment variables with defaults
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Optional[str] = os.getenv("BOT_USERNAME", "YourBotName")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))

# Default prompt for AI responses
DEFAULT_PROMPT: str = os.getenv(
    "DEFAULT_PROMPT",
    """You are a helpful AI assistant. Respond to the user's message like a dude bro, but informative and concise. Be helpful and accurate in your responses."""
)

# Plugin configuration
ENABLED_PLUGINS: list = os.getenv("ENABLED_PLUGINS", "telegram,web_search,discord").split(",")

# Discord configuration
DISCORD_BOT_TOKEN: Optional[str] = os.getenv("DISCORD_BOT_TOKEN")

# LLM Provider configuration
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, groq
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

# Validate required settings
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

if not OLLAMA_HOST:
    raise ValueError("OLLAMA_HOST environment variable is required")
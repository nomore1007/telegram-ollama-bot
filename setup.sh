#!/bin/bash

# Bot Setup Script
echo "🤖 Telegram Ollama Bot Setup"
echo "============================"

# Check if token is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <your_telegram_bot_token>"
    echo ""
    echo "📝 How to get your token:"
    echo "1. Message @BotFather on Telegram"
    echo "2. Send: /newbot"
    echo "3. Copy the token provided"
    echo "4. Run: $0 YOUR_TOKEN_HERE"
    exit 1
fi

TOKEN="$1"

echo "✅ Token received (length: ${#TOKEN})"

# Create settings.py with the token
cat > settings.py << EOF
# Bot Configuration - Created by setup.sh
# This file contains sensitive information and is excluded from version control

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN: str = "$TOKEN"

# Bot Identity
BOT_USERNAME: str = "DeepthoughtBot"

# Ollama AI Configuration
OLLAMA_HOST: str = "http://localhost:11434"
OLLAMA_MODEL: str = "llama2"

# AI Model Parameters
MAX_TOKENS: int = 2000
TEMPERATURE: float = 0.7
TIMEOUT: int = 30

# Default AI Prompt
DEFAULT_PROMPT: str = """You are a helpful AI assistant. Respond to the user's message like a dude bro, but informative and concise. Be helpful and accurate in your responses."""

# Validate required settings
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

if not OLLAMA_HOST:
    raise ValueError("OLLAMA_HOST is required")
EOF

echo "✅ Settings.py created with your token"

# Set environment variable as backup
export TELEGRAM_BOT_TOKEN="$TOKEN"
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama2"

echo "✅ Environment variables set"

# Test import using a simpler approach
echo ""
echo "🔧 Testing bot imports..."

# Create a temporary Python test script
PROJECT_DIR="$(pwd)"
cat > /tmp/test_imports.py << EOF
import sys, os

# Add project directory to path
sys.path.insert(0, '$PROJECT_DIR')

# Load settings directly (same as bot.py)
settings_path = os.path.join('$PROJECT_DIR', 'settings.py')
if os.path.exists(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        exec(f.read(), globals())
else:
    print(f'Settings file not found at {settings_path}')
    exit(1)

try:
    print('Settings loaded')

    from constants import MAX_MESSAGE_LENGTH
    print('Constants imported')

    from ollama_client import OllamaClient
    print('Ollama client imported')

    from conversation import ConversationManager
    print('Conversation manager imported')

    from security import InputValidator
    print('Security modules imported')

    print('')
    print('All imports successful!')
    print('')
    print('Ready to run the bot!')

except Exception as e:
    print(f'Import failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
EOF

if python3 /tmp/test_imports.py; then
    echo ""
    echo "💡 Next steps:"
    echo "1. Make sure Ollama is running: ollama list"
    echo "2. Run the bot: export TELEGRAM_BOT_TOKEN=\"$TOKEN\" && python bot.py"
    echo "3. Test on Telegram by messaging your bot!"

    # Cleanup
    rm /tmp/test_imports.py
else
    echo "❌ Setup failed"
    rm /tmp/test_imports.py
    exit 1
fi
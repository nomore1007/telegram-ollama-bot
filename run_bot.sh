#!/bin/bash

# Telegram Ollama Bot Runner
# This script activates the virtual environment and runs the bot

echo "🤖 Telegram Ollama Bot Launcher"
echo "==============================="

# Check if virtual environment exists
if [ ! -d "bot_env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python -m venv bot_env && source bot_env/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if settings.py exists and has a token
if [ ! -f "config.py" ] || ! grep -q "TELEGRAM_BOT_TOKEN.*=" config.py 2>/dev/null; then
    echo "⚠️  config.py not found or invalid!"
    echo "Run: ./setup.sh YOUR_TELEGRAM_TOKEN"
    echo ""
    echo "Get your token from: https://t.me/botfather"
    exit 1
fi

# Extract token from settings.py for environment variable
TOKEN_FROM_SETTINGS=$(grep "TELEGRAM_BOT_TOKEN.*=" config.py | sed 's/.*= *"*\([^"]*\)"*/\1/' | tr -d "'\"")
if [ -n "$TOKEN_FROM_SETTINGS" ]; then
    export TELEGRAM_BOT_TOKEN="$TOKEN_FROM_SETTINGS"
    echo "✅ Token loaded from config.py"
else
    echo "❌ Could not extract token from config.py"
    exit 1
fi

# Activate virtual environment and run bot
echo "🚀 Starting bot..."
source bot_env/bin/activate

# Set PYTHONPATH to include current directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

python bot.py
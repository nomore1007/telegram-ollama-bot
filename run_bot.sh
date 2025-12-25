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

# Check if token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  TELEGRAM_BOT_TOKEN environment variable not set!"
    echo "Set it with: export TELEGRAM_BOT_TOKEN='your_token_here'"
    echo ""
    echo "Get your token from: https://t.me/botfather"
    echo ""
    read -p "Do you want to continue with a test token? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export TELEGRAM_BOT_TOKEN="test_token_for_testing"
        echo "✅ Using test token (replace with real token for production)"
    else
        echo "❌ Please set TELEGRAM_BOT_TOKEN and run again"
        exit 1
    fi
fi

# Activate virtual environment and run bot
echo "🚀 Starting bot..."
source bot_env/bin/activate

# Set PYTHONPATH to include current directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

python bot.py
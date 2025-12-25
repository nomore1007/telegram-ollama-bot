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

# Set environment variable
export TELEGRAM_BOT_TOKEN="$TOKEN"
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama2"

echo "✅ Environment variables set"

# Test import
echo ""
echo "🔧 Testing bot imports..."
if python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
try:
    import settings
    print('✅ Settings imported')
    
    from constants import MAX_MESSAGE_LENGTH
    print('✅ Constants imported')
    
    from ollama_client import OllamaClient
    print('✅ Ollama client imported')
    
    from conversation import ConversationManager
    print('✅ Conversation manager imported')
    
    from security import InputValidator
    print('✅ Security modules imported')
    
    print('')
    print('🎉 All imports successful!')
    print('')
    print('🚀 Ready to run the bot!')
    print('Run: export TELEGRAM_BOT_TOKEN=\"$TOKEN\" && python bot.py')
    
except Exception as e:
    print(f'❌ Import failed: {e}')
    exit 1
"; then
    echo ""
    echo "💡 Next steps:"
    echo "1. Make sure Ollama is running: ollama list"
    echo "2. Run the bot: export TELEGRAM_BOT_TOKEN=\"$TOKEN\" && python bot.py"
    echo "3. Test on Telegram by messaging your bot!"
else
    echo "❌ Setup failed"
    exit 1
fi
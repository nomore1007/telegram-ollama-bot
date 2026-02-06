#!/bin/bash

# Quick test script to verify bot setup
echo "🧪 Testing bot setup..."

# Check if settings.py exists
if [ ! -f "config.py" ]; then
    echo "❌ config.py not found. Run: cp config.example.py config.py"
    exit 1
fi

# Try to import settings (this will fail if token not set)
echo "🔧 Testing Python imports..."
if python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
try:
    import config
    print('✅ Config imported successfully')
    print(f'   Token configured: {bool(config.TELEGRAM_BOT_TOKEN)}')
    print(f'   Ollama host: {config.OLLAMA_HOST}')
    print(f'   Model: {config.OLLAMA_MODEL}')
except Exception as e:
    print(f'❌ Settings error: {e}')
    exit(1)
"; then
    echo ""
    echo "🎉 Setup looks good!"
    echo "Try running: python bot.py"
else
    echo "❌ Setup test failed"
    exit 1
fi
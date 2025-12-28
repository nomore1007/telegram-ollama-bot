#!/usr/bin/env python3
"""Simple test script to verify bot imports work"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 Testing bot imports...")

try:
    # Test basic imports
    import settings
    print("✅ settings module imported")

    from constants import MAX_MESSAGE_LENGTH
    print(f"✅ constants imported (MAX_MESSAGE_LENGTH: {MAX_MESSAGE_LENGTH})")

    from ollama_client import OllamaClient
    print("✅ ollama_client imported")

    from conversation import ConversationManager
    print("✅ conversation imported")

    from security import InputValidator
    print("✅ security imported")

    # Test settings values
    print(f"📋 TELEGRAM_BOT_TOKEN configured: {bool(settings.TELEGRAM_BOT_TOKEN)}")
    print(f"📋 OLLAMA_HOST: {settings.OLLAMA_HOST}")
    print(f"📋 OLLAMA_MODEL: {settings.OLLAMA_MODEL}")

    print("\n🎉 All imports successful!")
    print("The bot should now be able to run with: python bot.py")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Try installing missing dependencies:")
    print("pip install python-telegram-bot requests newspaper3k youtube-transcript-api pytube")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
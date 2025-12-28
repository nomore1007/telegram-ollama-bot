#!/usr/bin/env python3
"""Bot setup and import test script"""

import os
import sys

def setup_environment():
    """Guide user through environment setup"""
    print("🤖 Telegram Ollama Bot Setup")
    print("=" * 40)

    # Check if settings.py exists
    if not os.path.exists('settings.py'):
        print("❌ settings.py not found!")
        print("Run: cp settings.example.py settings.py")
        return False

    # Check for required environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        print("\n📝 To set it:")
        print("1. Get token from @BotFather on Telegram")
        print("2. Run: export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("3. Or edit settings.py directly")
        return False

    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    print(f"✅ TELEGRAM_BOT_TOKEN: {'*' * 20}...{telegram_token[-10:] if telegram_token else 'NOT SET'}")
    print(f"✅ OLLAMA_HOST: {ollama_host}")

    return True

def test_imports():
    """Test all bot imports"""
    print("\n🔧 Testing imports...")

    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    try:
        import settings
        print("✅ settings imported")

        from constants import MAX_MESSAGE_LENGTH
        print(f"✅ constants imported (MAX_MESSAGE_LENGTH: {MAX_MESSAGE_LENGTH})")

        from ollama_client import OllamaClient
        print("✅ ollama_client imported")

        from conversation import ConversationManager
        print("✅ conversation imported")

        from security import InputValidator, RateLimiter
        print("✅ security imported")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Try: pip install python-telegram-bot requests newspaper3k youtube-transcript-api pytube")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main setup function"""
    # Check environment first
    if not setup_environment():
        print("\n💡 Fix the issues above, then run this script again.")
        return

    # Test imports
    if test_imports():
        print("\n🎉 Setup complete! Run the bot with:")
        print("python bot.py")
        print("\nOr use the wrapper:")
        print("python run_bot.py")
    else:
        print("\n❌ Import test failed. Check dependencies.")

if __name__ == "__main__":
    main()
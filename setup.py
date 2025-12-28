#!/usr/bin/env python3
"""
Setup script for Deepthought Bot.

Helps users create their settings.py file from the example template.
"""

import os
import shutil
from pathlib import Path


def main():
    """Run the setup process."""
    print("🤖 Deepthought Bot Setup")
    print("=" * 40)

    settings_example = Path("settings.example.py")
    settings_file = Path("settings.py")

    if not settings_example.exists():
        print("❌ settings.example.py not found!")
        return

    if settings_file.exists():
        response = input("⚠️  settings.py already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    # Copy the example file
    shutil.copy(settings_example, settings_file)
    print("✅ Created settings.py from settings.example.py")

    print("\n📝 Next steps:")
    print("1. Edit settings.py with your actual configuration")
    print("2. Set your TELEGRAM_BOT_TOKEN (get from @BotFather)")
    print("3. Configure LLM provider settings if needed")
    print("4. Run: python admin_cli.py setup YOUR_USER_ID")
    print("5. Start the bot: python bot.py")

    print("\n🔒 Security reminder:")
    print("- settings.py contains sensitive information")
    print("- It is automatically ignored by Git")
    print("- Never share or commit settings.py")

    print("\n🚀 You're all set! Edit settings.py and run the bot.")


if __name__ == '__main__':
    main()
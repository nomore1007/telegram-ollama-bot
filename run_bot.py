#!/usr/bin/env python3
"""Wrapper script to run the Telegram Ollama Bot with correct imports"""

import sys
import os

# Add the directory containing this script to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Now import and run the bot
from bot import main

if __name__ == "__main__":
    if "--test" in sys.argv:
        main(test_mode=True)
    else:
        main()
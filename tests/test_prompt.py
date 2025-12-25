#!/usr/bin/env python3
"""
Test script for custom prompt functionality
"""
import sys
sys.path.append('/home/nomore/deepthought-bot')

from bot import TelegramOllamaBot, settings

def test_custom_prompt():
    print("🧪 Testing Custom Prompt Functionality...")
    
    # Initialize bot
    bot = TelegramOllamaBot(settings)
    
    # Test default prompt
    print(f"\n📝 Default Prompt: {bot.custom_prompt}")
    
    # Test different prompt lengths
    test_prompts = [
        "You are a helpful assistant.",  # Valid
        "Too short",  # Too short
        "You are a very detailed and comprehensive AI assistant who provides thorough explanations and considers multiple perspectives when answering questions.",  # Valid
        "A" * 1001,  # Too long
    ]
    
    print(f"\n🧪 Testing Prompt Validation:")
    for i, prompt in enumerate(test_prompts, 1):
        print(f"Test {i}: Length {len(prompt)} - {'✅ Valid' if 10 <= len(prompt) <= 1000 else '❌ Invalid'}")
        if i == 2:  # Valid long prompt
            print(f"  Preview: {prompt[:50]}...")
        elif i == 3:  # Too long prompt
            print(f"  Preview: {prompt[:20]}...")
    
    print("\n✅ Custom Prompt Test Complete!")

if __name__ == "__main__":
    test_custom_prompt()
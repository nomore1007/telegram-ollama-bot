#!/usr/bin/env python3
"""
Quick test script for news URL detection
"""
import sys
sys.path.append('/home/nomore/deepthought-bot')

from bot import NewsSummarizer, OllamaClient, settings

def test_url_detection():
    print("🧪 Testing News URL Detection...")
    
    # Initialize components
    ollama = OllamaClient(settings.OLLAMA_HOST, settings.OLLAMA_MODEL, settings.TIMEOUT)
    summarizer = NewsSummarizer(ollama)
    
    # Test URL extraction
    test_messages = [
        "Check out this BBC article: https://www.bbc.com/news/world-123456",
        "Here's a CNN story https://edition.cnn.com/2024/politics/article and a Reuters link https://reuters.com/world/article",
        "This is not a news link: https://github.com/user/repo",
        "Multiple news: https://www.bbc.com/news and https://www.nytimes.com/2024/article",
        "No URLs in this message",
    ]
    
    print("\n📋 Testing URL Detection:")
    for i, message in enumerate(test_messages, 1):
        urls = summarizer.extract_urls(message)
        print(f"Test {i}: Found {len(urls)} news URLs")
        for url in urls:
            print(f"  📰 {url}")
        print()
    
    print("✅ URL Detection Test Complete!")

if __name__ == "__main__":
    test_url_detection()
#!/usr/bin/env python3
"""
Test script for news summarization functionality
"""
import asyncio
import sys
sys.path.append('/home/nomore/deepthought-bot')

from ollama_client import OllamaClient
from summarizers import NewsSummarizer
import settings

async def test_news_summarization():
    print("🧪 Testing News Summarization...")
    
    # Initialize components
    ollama = OllamaClient(settings.OLLAMA_HOST, settings.OLLAMA_MODEL, settings.TIMEOUT)
    summarizer = NewsSummarizer(ollama)
    
    # Test URL extraction
    test_messages = [
        "Check out this BBC article: https://www.bbc.com/news",
        "Here's a CNN story https://edition.cnn.com/2024/some-article and a Reuters link https://reuters.com/world",
        "This is not a news link: https://github.com/user/repo",
    ]
    
    print("\n📋 Testing URL Detection:")
    for i, message in enumerate(test_messages, 1):
        urls = summarizer.extract_urls(message)
        print(f"Test {i}: Found {len(urls)} news URLs - {urls}")
    
    # Test with a real news URL (BBC for testing)
    test_url = "https://www.bbc.com/news"
    print(f"\n📰 Testing Article Extraction: {test_url}")
    
    article_data = await summarizer.extract_article_content(test_url)
    if article_data["success"]:
        print(f"✅ Title: {article_data['title'][:100]}...")
        print(f"✅ Content length: {len(article_data['text'])} characters")
        
        # Test summarization (this might take time)
        print("\n🤖 Testing AI Summarization...")
        summary = await summarizer.summarize_with_ai(article_data)
        print(f"✅ Summary generated: {len(summary)} characters")
        print(f"📝 Summary preview: {summary[:200]}...")
    else:
        print(f"❌ Extraction failed: {article_data['error']}")

if __name__ == "__main__":
    asyncio.run(test_news_summarization())
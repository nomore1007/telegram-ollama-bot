#!/usr/bin/env python3
"""
Test script for YouTube URL detection
"""
import sys
sys.path.append('/home/nomore/deepthought-bot')

from bot import YouTubeSummarizer, OllamaClient, settings

def test_youtube_detection():
    print("🧪 Testing YouTube URL Detection...")
    
    # Initialize components
    ollama = OllamaClient(settings.OLLAMA_HOST, settings.OLLAMA_MODEL, settings.TIMEOUT)
    summarizer = YouTubeSummarizer(ollama)
    
    # Test URL extraction
    test_messages = [
        "Check out this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Watch this short: https://youtu.be/abc123def",
        "Here's an embed: https://www.youtube.com/embed/xyz789abc",
        "This is not YouTube: https://www.bbc.com/news",
        "Multiple videos: https://www.youtube.com/watch?v=video1 and https://youtu.be/video2",
        "YouTube shorts: https://www.youtube.com/shorts/short123",
    ]
    
    print("\n📋 Testing YouTube URL Detection:")
    for i, message in enumerate(test_messages, 1):
        urls = summarizer.extract_video_urls(message)
        print(f"Test {i}: Found {len(urls)} YouTube URLs")
        for url in urls:
            video_id = summarizer.extract_video_id(url)
            print(f"  🎬 {url} -> ID: {video_id}")
        print()
    
    # Test video ID extraction specifically
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/abc123def",
        "https://www.youtube.com/embed/xyz789abc",
        "https://www.youtube.com/shorts/short123",
        "https://www.youtube.com/v/video123",
    ]
    
    print("\n🔍 Testing Video ID Extraction:")
    for url in test_urls:
        video_id = summarizer.extract_video_id(url)
        print(f"🎬 {url}\n   ID: {video_id}")
    
    print("\n✅ YouTube Detection Test Complete!")

if __name__ == "__main__":
    test_youtube_detection()
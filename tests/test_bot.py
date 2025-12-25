import pytest
from bot import NewsSummarizer, YouTubeSummarizer, OllamaClient


class TestNewsSummarizer:
    """Test news summarization functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        # Mock Ollama client for testing
        self.mock_ollama = OllamaClient("http://localhost:11434", "test-model")
        self.summarizer = NewsSummarizer(self.mock_ollama)

    def test_extract_urls_news_sites(self):
        """Test URL extraction for known news sites"""
        test_cases = [
            ("Check this BBC article: https://www.bbc.com/news", ["https://www.bbc.com/news"]),
            ("CNN story: https://edition.cnn.com/2024/news", ["https://edition.cnn.com/2024/news"]),
            ("Multiple sites: https://www.bbc.com/news and https://reuters.com/world",
             ["https://www.bbc.com/news", "https://reuters.com/world"]),
            ("No news sites: https://github.com/user/repo", []),
            ("Mixed: https://www.bbc.com/news and https://github.com/user/repo",
             ["https://www.bbc.com/news"]),
        ]

        for message, expected in test_cases:
            urls = self.summarizer.extract_urls(message)
            assert urls == expected, f"Failed for message: {message}"

    def test_extract_urls_case_insensitive(self):
        """Test URL extraction is case insensitive"""
        message = "Check BBC: https://WWW.BBC.COM/NEWS"
        urls = self.summarizer.extract_urls(message)
        assert urls == ["https://WWW.BBC.COM/NEWS"]


class TestYouTubeSummarizer:
    """Test YouTube summarization functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_ollama = OllamaClient("http://localhost:11434", "test-model")
        self.summarizer = YouTubeSummarizer(self.mock_ollama)

    def test_extract_video_urls(self):
        """Test YouTube URL extraction"""
        test_cases = [
            ("Watch this: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
             ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]),
            ("Short video: https://youtu.be/dQw4w9WgXcQ",
             ["https://youtu.be/dQw4w9WgXcQ"]),
            ("Embed: https://www.youtube.com/embed/dQw4w9WgXcQ",
             ["https://www.youtube.com/embed/dQw4w9WgXcQ"]),
            ("No YouTube: https://github.com/user/repo", []),
        ]

        for message, expected in test_cases:
            urls = self.summarizer.extract_video_urls(message)
            assert urls == expected, f"Failed for message: {message}"

    def test_extract_video_id(self):
        """Test video ID extraction from various YouTube URL formats"""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/v/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://invalid.url", None),
        ]

        for url, expected in test_cases:
            video_id = self.summarizer.extract_video_id(url)
            assert video_id == expected, f"Failed for URL: {url}"


class TestOllamaClient:
    """Test Ollama client functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = OllamaClient("http://localhost:11434", "test-model", timeout=5)

    def test_initialization(self):
        """Test client initialization"""
        assert self.client.host == "http://localhost:11434"
        assert self.client.model == "test-model"
        assert self.client.timeout == 5
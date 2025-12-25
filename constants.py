"""Constants and configuration values"""

# Message limits
MAX_MESSAGE_LENGTH = 4000
MAX_ARTICLES_PER_MESSAGE = 2
MAX_VIDEOS_PER_MESSAGE = 2

# API timeouts and retries
OLLAMA_DEFAULT_TIMEOUT = 30
OLLAMA_MAX_RETRIES = 3

# Transcript settings
TRANSCRIPT_MAX_LENGTH = 4000

# Article processing
ARTICLE_MAX_TEXT_LENGTH = 4000

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Supported news sites (regex patterns)
NEWS_SITE_PATTERNS = [
    r'bbc\.com',
    r'cnn\.com',
    r'reuters\.com',
    r'nytimes\.com',
    r'washingtonpost\.com',
    r'guardian\.com',
    r'theguardian\.com',
    r'wsj\.com',
    r'bloomberg\.com',
    r'nbcnews\.com',
    r'abcnews\.go\.com',
    r'cbsnews\.com',
    r'foxnews\.com',
    r'apnews\.com',
    r'npr\.org',
    r'vox\.com',
    r'politico\.com',
    r'wired\.com',
    r'techcrunch\.com',
    r'engadget\.com',
    r'thesun\.co\.uk',
    r'dailymail\.co\.uk',
    r'mirror\.co\.uk',
    r'independent\.co\.uk',
    r'ft\.com',
    r'economist\.com',
    r'time\.com',
    r'news\.yahoo\.com',
    r'news\.google\.com',
]

# YouTube URL patterns
YOUTUBE_URL_PATTERNS = [
    r'youtube\.com/watch\?v=[\w-]+',
    r'youtube\.com/embed/[\w-]+',
    r'youtube\.com/v/[\w-]+',
    r'youtu\.be/[\w-]+',
    r'youtube\.com/shorts/[\w-]+',
]